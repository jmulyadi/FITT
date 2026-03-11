// ─────────────────────────────────────────────────────────────────────────────
// Nutrition.jsx
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useEffect, useMemo, useRef } from 'react'
import AICard from '../components/AICard'
import {
  getTodaysMeals, getMealsByDate, createMeal, updateMealCalories,
  deleteMeal, addFoodToMeal, updateFoodItem, deleteFoodItem, searchFood
} from '../api/nutrition'

const DEFAULT_MEAL_NAMES = { 1: 'Breakfast', 2: 'Lunch', 3: 'Dinner', 4: 'Snack', 5: 'Snack 2' }
const MEAL_ICONS = { 1: '🌅', 2: '☀️', 3: '🌙', 4: '🍎', 5: '🥜' }
const MEAL_BGS   = { 1: '#f59e0b22', 2: '#3b82f622', 3: '#6366f122', 4: '#22c55e22', 5: '#ec489922' }
const CALORIE_GOAL = 2400

const todayStr = () => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const fmtDate = (iso) => {
  const [y, m, d] = iso.split('-')
  const dt = new Date(+y, +m - 1, +d)
  return dt.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

// ── MacroBar ──────────────────────────────────────────────────────────────────
function MacroBar({ current, goal }) {
  const pct = Math.min(100, Math.round((current / goal) * 100))
  const over = current > goal
  return (
    <div className="macro-bar-wrap">
      <div className="macro-label-row">
        <span>Calories</span>
        <span>{current} / {goal} kcal</span>
      </div>
      <div className="macro-bar">
        <div className="macro-fill fill-blue" style={{ width: `${pct}%`, background: over ? '#ef4444' : undefined }} />
      </div>
    </div>
  )
}

// ── Food Search Sheet ─────────────────────────────────────────────────────────
function FoodSearchSheet({ mealId, onClose, onAdded }) {
  const [query, setQuery]       = useState('')
  const [results, setResults]   = useState([])
  const [searching, setSearching] = useState(false)
  const [saving, setSaving]     = useState(null)
  const [qtys, setQtys]         = useState({})
  const debounceRef             = useRef(null)

  const handleSearch = (q) => {
    setQuery(q)
    setQtys({})
    if (!q.trim() || q.length < 3) { setResults([]); return }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        const data = await searchFood(q)
        setResults(data.products || [])
      } catch (e) { console.error(e) }
      finally { setSearching(false) }
    }, 600)
  }

  const handleAdd = async (product, idx) => {
    setSaving(idx)
    const isServingBased = product.calories_per_serving != null
    const rawQ = qtys[idx] ?? (isServingBased ? '1' : '100')
    const parsedQ = parseFloat(rawQ)
    const safeQ = (!rawQ || isNaN(parsedQ) || parsedQ <= 0) ? (isServingBased ? 1 : 100) : parsedQ
    const totalCal = isServingBased
      ? Math.round((product.calories_per_serving ?? 0) * safeQ)
      : Math.round((product.calories_per_100g ?? 0) * safeQ / 100)
    try {
      const saved = await addFoodToMeal(mealId, product.name || 'Unknown', 'Other', totalCal)
      onAdded(saved, totalCal)
    } catch (e) { console.error(e) }
    finally { setSaving(null) }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 300, background: 'rgba(0,0,0,0.65)', display: 'flex', alignItems: 'flex-end' }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div style={{ background: 'var(--card)', borderRadius: '18px 18px 0 0', width: '100%', maxHeight: '82vh', display: 'flex', flexDirection: 'column', padding: '20px 16px 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h3 style={{ margin: 0, fontSize: 17 }}>Search Food</h3>
          <button className="btn btn-ghost" style={{ padding: '4px 12px', fontSize: 13 }} onClick={onClose}>Cancel</button>
        </div>
        <input autoFocus type="text" placeholder="Search food (e.g. chicken breast, oats)"
          value={query} onChange={e => handleSearch(e.target.value)}
          style={{ width: '100%', padding: '10px 14px', fontSize: 15, borderRadius: 10, border: '1.5px solid var(--border)', background: 'var(--bg)', color: 'var(--text)', marginBottom: 12, boxSizing: 'border-box' }} />
        <div style={{ overflowY: 'auto', flex: 1, paddingBottom: 32 }}>
          {searching && <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 24, fontSize: 14 }}>Searching...</div>}
          {!searching && query.length >= 3 && results.length === 0 && <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 24, fontSize: 14 }}>No results for "{query}"</div>}
          {(!query || query.length < 3) && <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 24, fontSize: 14 }}>Type at least 3 characters to search</div>}
          {results.map((p, i) => {
            const isServingBased = p.calories_per_serving != null
            const baseLabel = isServingBased
              ? `${Math.round(p.calories_per_serving)} kcal / ${p.serving_size || '1 serving'}`
              : `${Math.round(p.calories_per_100g ?? 0)} kcal / 100g`
            const rawQty = qtys[i] ?? (isServingBased ? '1' : '100')
            const qty = parseFloat(rawQty)
            const safeQty = (!rawQty || isNaN(qty) || qty <= 0) ? (isServingBased ? 1 : 100) : qty
            const previewCal = isServingBased
              ? Math.round((p.calories_per_serving ?? 0) * safeQty)
              : Math.round((p.calories_per_100g ?? 0) * safeQty / 100)
            return (
              <div key={i} style={{ padding: '10px 4px', borderBottom: '1px solid var(--border)' }}>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>{p.brand ? `${p.brand} · ` : ''}{baseLabel}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input type="number" min="0.1" step={isServingBased ? '0.5' : '10'} value={rawQty}
                    onChange={e => setQtys(prev => ({ ...prev, [i]: e.target.value }))}
                    style={{ width: 64, padding: '5px 8px', fontSize: 13, borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text)', textAlign: 'center' }} />
                  <span style={{ fontSize: 12, color: 'var(--muted)' }}>{isServingBased ? 'serving(s)' : 'g'}</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--green)', marginLeft: 4 }}>= {previewCal} kcal</span>
                  <button className="btn btn-green" style={{ padding: '6px 16px', fontSize: 13, flexShrink: 0, marginLeft: 'auto' }}
                    disabled={saving === i} onClick={() => handleAdd(p, i)}>
                    {saving === i ? '...' : '+ Add'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Inline Meal Name Editor ───────────────────────────────────────────────────
function MealNameEditor({ mealId, defaultName, customNames, onRename, readOnly }) {
  const [editing, setEditing] = useState(false)
  const [val, setVal]         = useState(customNames[mealId] ?? defaultName)
  const inputRef              = useRef(null)

  useEffect(() => { setVal(customNames[mealId] ?? defaultName) }, [customNames, mealId, defaultName])
  useEffect(() => { if (editing) inputRef.current?.select() }, [editing])

  if (readOnly) return <div className="meal-name">{customNames[mealId] ?? defaultName}</div>

  const commit = () => {
    const trimmed = val.trim() || defaultName
    setVal(trimmed)
    onRename(mealId, trimmed)
    setEditing(false)
  }

  if (editing) return (
    <input ref={inputRef} value={val} onChange={e => setVal(e.target.value)}
      onBlur={commit} onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') { setVal(customNames[mealId] ?? defaultName); setEditing(false) } }}
      style={{ fontSize: 15, fontWeight: 700, background: 'transparent', border: 'none', borderBottom: '1.5px solid var(--accent)', outline: 'none', color: 'var(--text)', width: 150, padding: '0 2px' }} />
  )
  return (
    <div className="meal-name" onClick={() => setEditing(true)} title="Tap to rename"
      style={{ cursor: 'text', display: 'flex', alignItems: 'center', gap: 5 }}>
      {customNames[mealId] ?? defaultName}
      <span style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 400 }}>✎</span>
    </div>
  )
}

// ── Food Servings Editor ─────────────────────────────────────────────────────
// Stores base-calories-per-serving in localStorage when food is first added,
// then lets user adjust servings to rescale calories.
function getBaseCalKey(foodId) { return `baseCal_${foodId}` }
function storeBaseCal(foodId, cal) {
  try { localStorage.setItem(getBaseCalKey(foodId), String(cal)) } catch {}
}
function loadBaseCal(foodId) {
  try { return parseFloat(localStorage.getItem(getBaseCalKey(foodId))) || null } catch { return null }
}

function FoodServingsEditor({ food, mealId, onUpdate, readOnly }) {
  const baseCal = loadBaseCal(food.food_id) ?? food.calories  // per-serving base
  const currentServings = baseCal > 0 ? food.calories / baseCal : 1

  const [editing, setEditing]   = useState(false)
  const [val, setVal]           = useState(currentServings.toFixed(2).replace(/\.?0+$/, '') || '1')
  const inputRef                = useRef(null)

  useEffect(() => {
    const s = baseCal > 0 ? food.calories / baseCal : 1
    setVal(String(parseFloat(s.toFixed(2))))
  }, [food.calories])
  useEffect(() => { if (editing) inputRef.current?.select() }, [editing])

  if (readOnly) return <span style={{ fontSize: 13, fontWeight: 600 }}>{food.calories} kcal</span>

  const commit = async () => {
    const parsed = parseFloat(val)
    const servings = isNaN(parsed) || parsed <= 0 ? currentServings : parsed
    const newCal = Math.round(baseCal * servings)
    setVal(String(parseFloat(servings.toFixed(2))))
    setEditing(false)
    if (newCal !== food.calories) {
      await onUpdate(food.food_id, newCal, food.calories)
    }
  }

  const previewCal = () => {
    const s = parseFloat(val)
    if (isNaN(s) || s <= 0) return food.calories
    return Math.round(baseCal * s)
  }

  if (editing) return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
      <input ref={inputRef} type="number" min="0.1" step="0.5" value={val}
        onChange={e => setVal(e.target.value)}
        onBlur={commit}
        onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') { setEditing(false) } }}
        style={{ width: 54, padding: '3px 6px', fontSize: 13, borderRadius: 6, border: '1px solid var(--accent)', background: 'var(--bg)', color: 'var(--text)', textAlign: 'center' }} />
      <span style={{ fontSize: 11, color: 'var(--muted)' }}>srv</span>
      <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--green)' }}>{previewCal()} kcal</span>
    </div>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
      <span onClick={() => setEditing(true)} title="Tap to adjust servings"
        style={{ fontSize: 13, fontWeight: 600, cursor: 'pointer', borderBottom: '1px dashed var(--muted)', paddingBottom: 1 }}>
        {food.calories} kcal
      </span>
      <span style={{ fontSize: 10, color: 'var(--muted)' }}>
        {parseFloat(currentServings.toFixed(2))} srv ✎
      </span>
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function Nutrition() {
  const [meals, setMeals]               = useState([])
  const [loading, setLoading]           = useState(true)
  const [selectedDate, setSelectedDate] = useState(todayStr())
  const [searchMealId, setSearchMealId] = useState(null)
  const [addingMeal, setAddingMeal]     = useState(false)
  const [deletingMeal, setDeletingMeal] = useState(null)
  const [deletingFood, setDeletingFood] = useState(null)
  const [customNames, setCustomNames]   = useState(() => {
    try { return JSON.parse(localStorage.getItem('mealNames') || '{}') } catch { return {} }
  })

  const isToday = selectedDate === todayStr()

  const loadMeals = (date) => {
    setLoading(true)
    getMealsByDate(date)
      .then(data => setMeals(Array.isArray(data) ? data : []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadMeals(selectedDate) }, [selectedDate])

  const totalCal = useMemo(() => meals.reduce((sum, m) => sum + (m.calories_in || 0), 0), [meals])
  const remaining = CALORIE_GOAL - totalCal

  const handleRename = (mealId, newName) => {
    setCustomNames(prev => {
      const next = { ...prev, [mealId]: newName }
      try { localStorage.setItem('mealNames', JSON.stringify(next)) } catch {}
      return next
    })
  }

  const handleFoodAdded = async (savedFood, calories) => {
    const meal = meals.find(m => m.meal_id === searchMealId)
    if (!meal) return
    const newCal = (meal.calories_in || 0) + calories
    try { await updateMealCalories(meal.meal_id, newCal) } catch (e) { console.error(e) }
    // Store base-cal-per-serving so the servings editor can use it later
    if (savedFood?.food_id) storeBaseCal(savedFood.food_id, calories)
    setMeals(prev => prev.map(m =>
      m.meal_id !== searchMealId ? m : { ...m, calories_in: newCal, food: [...(m.food || []), savedFood] }
    ))
    setSearchMealId(null)
  }

  const handleUpdateFood = async (foodId, newCal, oldCal) => {
    // Find which meal this food belongs to
    const meal = meals.find(m => (m.food || []).some(f => f.food_id === foodId))
    if (!meal) return
    try {
      await updateFoodItem(meal.meal_id, foodId, newCal)
      const mealNewCal = Math.max(0, (meal.calories_in || 0) - oldCal + newCal)
      await updateMealCalories(meal.meal_id, mealNewCal)
      setMeals(prev => prev.map(m =>
        m.meal_id !== meal.meal_id ? m : {
          ...m,
          calories_in: mealNewCal,
          food: m.food.map(f => f.food_id === foodId ? { ...f, calories: newCal } : f)
        }
      ))
    } catch (e) { console.error(e) }
  }

  const handleAddMeal = async () => {
    const usedNums = new Set(meals.map(m => m.meal_num))
    const next = [1, 2, 3, 4, 5].find(n => !usedNums.has(n))
    if (!next) return
    setAddingMeal(true)
    try {
      const { meal_id } = await createMeal(next, 0)
      setMeals(prev => [...prev, { meal_id, meal_num: next, calories_in: 0, food: [] }]
        .sort((a, b) => a.meal_num - b.meal_num))
    } catch (e) { console.error(e) }
    finally { setAddingMeal(false) }
  }

  const handleDeleteMeal = async (e, mealId) => {
    e.stopPropagation()
    if (!window.confirm('Delete this meal?')) return
    setDeletingMeal(mealId)
    try {
      await deleteMeal(mealId)
      setMeals(prev => prev.filter(m => m.meal_id !== mealId))
      setCustomNames(prev => {
        const n = { ...prev }; delete n[mealId]
        try { localStorage.setItem('mealNames', JSON.stringify(n)) } catch {}
        return n
      })
    } catch (e) { console.error(e) }
    finally { setDeletingMeal(null) }
  }

  const handleDeleteFood = async (e, mealId, foodId, foodCal) => {
    e.stopPropagation()
    setDeletingFood(foodId)
    try {
      await deleteFoodItem(mealId, foodId)
      const meal = meals.find(m => m.meal_id === mealId)
      const newCal = Math.max(0, (meal?.calories_in || 0) - foodCal)
      await updateMealCalories(mealId, newCal)
      setMeals(prev => prev.map(m =>
        m.meal_id !== mealId ? m : {
          ...m, calories_in: newCal,
          food: (m.food || []).filter(f => f.food_id !== foodId)
        }
      ))
    } catch (e) { console.error(e) }
    finally { setDeletingFood(null) }
  }

  const changeDate = (delta) => {
    const d = new Date(selectedDate + 'T12:00:00')
    d.setDate(d.getDate() + delta)
    const next = d.toISOString().split('T')[0]
    if (next <= todayStr()) setSelectedDate(next)
  }

  const digest = useMemo(() => {
    if (!isToday) return null
    if (!meals.length) return "No meals logged today. Start by adding a meal below."
    const pct = Math.round((totalCal / CALORIE_GOAL) * 100)
    if (pct < 50) return `You've had ${totalCal} kcal so far — ${pct}% of your daily goal. Make sure to eat enough to fuel your training.`
    if (pct < 90) return `${totalCal} kcal consumed — on track. ${remaining} kcal remaining to hit your ${CALORIE_GOAL} kcal goal.`
    if (pct <= 100) return `Almost at your goal — ${totalCal} kcal of ${CALORIE_GOAL}. Great work staying on target.`
    return `You've exceeded your calorie goal by ${Math.abs(remaining)} kcal today.`
  }, [meals, totalCal, remaining, isToday])

  return (
    <div className="page fade-in">
      <div className="page-header"><h1>Nutrition</h1></div>
      <div className="page-content">
        <div style={{ height: 14 }} />

        {isToday && digest && <AICard>{digest}</AICard>}

        {/* ── Date navigator ── */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, background: 'var(--card)', borderRadius: 14, padding: '10px 16px' }}>
          <button onClick={() => changeDate(-1)}
            style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text)', padding: '0 8px', lineHeight: 1 }}>‹</button>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 15, fontWeight: 700 }}>{isToday ? 'Today' : fmtDate(selectedDate)}</div>
            {!isToday && <div style={{ fontSize: 11, color: 'var(--muted)' }}>{selectedDate}</div>}
          </div>
          <button onClick={() => changeDate(1)}
            disabled={isToday}
            style={{ background: 'none', border: 'none', fontSize: 20, cursor: isToday ? 'default' : 'pointer', color: isToday ? 'var(--muted)' : 'var(--text)', padding: '0 8px', lineHeight: 1, opacity: isToday ? 0.3 : 1 }}>›</button>
        </div>

        {/* ── Daily summary ── */}
        <div className="card fade-in">
          <div className="card-title">Daily Summary</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 36, fontWeight: 900, lineHeight: 1 }}>{totalCal.toLocaleString()}</div>
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>/ {CALORIE_GOAL.toLocaleString()} kcal</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 12, color: 'var(--muted)' }}>{remaining >= 0 ? 'Remaining' : 'Over goal'}</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: remaining >= 0 ? 'var(--green)' : '#ef4444' }}>
                {Math.abs(remaining).toLocaleString()}
              </div>
            </div>
          </div>
          <MacroBar current={totalCal} goal={CALORIE_GOAL} />
        </div>

        {/* ── Meals ── */}
        {loading ? (
          <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 24, fontSize: 14 }}>Loading...</div>
        ) : (
          <div className="card fade-in">
            <div className="card-title">{isToday ? "Today's Meals" : `Meals — ${fmtDate(selectedDate)}`}</div>

            {meals.length === 0 && (
              <div style={{ color: 'var(--muted)', fontSize: 13, padding: '8px 0' }}>
                {isToday ? 'No meals logged yet.' : 'No meals logged on this day.'}
              </div>
            )}

            {meals.map(meal => {
              const defaultName = DEFAULT_MEAL_NAMES[meal.meal_num] || `Meal ${meal.meal_num}`
              return (
                <div key={meal.meal_id} style={{ marginBottom: 16 }}>
                  {/* Meal header */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <div className="meal-icon" style={{ background: MEAL_BGS[meal.meal_num] || '#3b82f622' }}>
                      {MEAL_ICONS[meal.meal_num] || '🍽️'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <MealNameEditor mealId={meal.meal_id} defaultName={defaultName}
                        customNames={customNames} onRename={handleRename} readOnly={!isToday} />
                      <div className="meal-sub">{meal.calories_in} kcal</div>
                    </div>
                    {isToday && (
                      <>
                        <button className="btn btn-ghost" style={{ fontSize: 12, padding: '4px 10px' }}
                          onClick={() => setSearchMealId(meal.meal_id)}>+ Food</button>
                        <button onClick={e => handleDeleteMeal(e, meal.meal_id)} disabled={deletingMeal === meal.meal_id}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', fontSize: 15, opacity: deletingMeal === meal.meal_id ? 0.4 : 0.7 }}>✕</button>
                      </>
                    )}
                  </div>

                  {/* Food items */}
                  {(meal.food || []).map(f => (
                    <div key={f.food_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0 6px 44px', borderBottom: '1px solid var(--border)' }}>
                      <div style={{ flex: 1, minWidth: 0, marginRight: 8 }}>
                        <div style={{ fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--muted)' }}>{f.type}</div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                        <FoodServingsEditor food={f} mealId={meal.meal_id} onUpdate={handleUpdateFood} readOnly={!isToday} />
                        {isToday && (
                          <button onClick={e => handleDeleteFood(e, meal.meal_id, f.food_id, f.calories)}
                            disabled={deletingFood === f.food_id}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', fontSize: 13, opacity: deletingFood === f.food_id ? 0.4 : 0.7 }}>✕</button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )
            })}

            {isToday && meals.length < 5 && (
              <button className="btn btn-ghost" style={{ width: '100%', marginTop: 8 }}
                onClick={handleAddMeal} disabled={addingMeal}>
                {addingMeal ? 'Adding...' : '+ Add Meal'}
              </button>
            )}
          </div>
        )}
      </div>

      {searchMealId && (
        <FoodSearchSheet mealId={searchMealId} onClose={() => setSearchMealId(null)} onAdded={handleFoodAdded} />
      )}
    </div>
  )
}