// Formatos de texto compartidos por varios archivos.

// 9.5 -> "9 h 30 min", 9 -> "9 h", 0.75 -> "45 min".
// Debe dar lo mismo que formato_duracion() en app/services/pdf_service.py.
function formatoDuracion(horas) {
  const totalMin = Math.round(Number(horas) * 60);
  if (!Number.isFinite(totalMin)) return "—";
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  if (h && m) return `${h} h ${m} min`;
  if (h) return `${h} h`;
  return `${m} min`;
}
