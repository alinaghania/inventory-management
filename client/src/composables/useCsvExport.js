/**
 * CSV export shared by the data-table views.
 *
 * Callers declare columns as `{ header, value }` pairs so an export carries the
 * labels the user sees but the raw numbers underneath them: a spreadsheet can
 * sum "1234.50" but not "$1,234.50".
 */

// Leading characters that spreadsheet apps treat as the start of a formula.
const FORMULA_PREFIXES = ['=', '+', '-', '@', '\t', '\r']

const needsFormulaGuard = (value) => {
  if (!FORMULA_PREFIXES.includes(value.charAt(0))) return false

  // "-12.5" and "+3" are data, not formulas. Guarding them would push a leading
  // quote into numeric columns and force the whole column to import as text.
  return !Number.isFinite(Number(value))
}

const escapeCell = (raw) => {
  const value = raw === null || raw === undefined ? '' : String(raw)

  // Excel and Sheets evaluate a cell beginning with '=' or '@', so untrusted
  // text can become executable input. A leading apostrophe forces literal text.
  const guarded = needsFormulaGuard(value) ? `'${value}` : value

  // RFC 4180: quote a field containing a delimiter, quote or line break, and
  // escape embedded quotes by doubling them.
  return /[",\r\n]/.test(guarded) ? `"${guarded.replace(/"/g, '""')}"` : guarded
}

const toCsv = (columns, rows) => {
  const lines = [columns.map((column) => escapeCell(column.header)).join(',')]

  for (const row of rows) {
    lines.push(columns.map((column) => escapeCell(column.value(row))).join(','))
  }

  // RFC 4180 mandates CRLF; Excel on Windows is the strictest consumer here.
  return lines.join('\r\n')
}

export function useCsvExport() {
  /**
   * Build a CSV from `rows` and hand it to the browser as a download.
   *
   * @param {string} filename  Base name, without extension or date suffix.
   * @param {Array<{header: string, value: (row: any) => any}>} columns
   * @param {Array<any>} rows
   * @returns {boolean} false when there was nothing to export.
   */
  const exportCsv = (filename, columns, rows) => {
    if (!rows || rows.length === 0) return false

    // Excel only detects UTF-8 from a byte-order mark. Without it the Japanese
    // locale's exports open as mojibake.
    const blob = new Blob(['\uFEFF' + toCsv(columns, rows)], {
      type: 'text/csv;charset=utf-8;'
    })

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const datestamp = new Date().toISOString().slice(0, 10)

    link.href = url
    link.download = `${filename}-${datestamp}.csv`

    // Firefox ignores click() on an anchor that is not in the document.
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    return true
  }

  return { exportCsv }
}
