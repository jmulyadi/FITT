import { apiFetch } from "./clients";

export async function getTemplates() {
  return apiFetch("/templates/");
}

export async function createTemplate(name, exercises) {
  return apiFetch("/templates/", {
    method: "POST",
    body: JSON.stringify({ name, exercises }),
  });
}

export async function deleteTemplate(templateId) {
  return apiFetch(`/templates/${templateId}`, { method: "DELETE" });
}

export async function updateTemplate(templateId, updates) {
  return apiFetch(`/templates/${templateId}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}
