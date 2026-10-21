/**
 * CSV Utility: Export, Parse, and Duplicate Validation
 */
const CSVUtil = {
  downloadCSV(arg1, arg2) {
    let filename = "export.csv";
    let rows = [];
    if (typeof arg1 === "string" && Array.isArray(arg2)) {
      filename = arg1;
      rows = arg2;
    } else if (Array.isArray(arg1) && typeof arg2 === "string") {
      rows = arg1;
      filename = arg2;
    } else if (Array.isArray(arg1)) {
      rows = arg1;
    }

    if (!rows || !rows.length) {
      if (window.App && typeof App.toast === "function") {
        App.toast("No records to export.", "warning");
      } else {
        alert("No records to export.");
      }
      return;
    }
    const headers = Object.keys(rows[0]);
    const csvContent = [
      headers.join(","),
      ...rows.map(row =>
        headers.map(field => {
          let val = row[field];
          if (val === null || val === undefined) val = "";
          val = String(val).replace(/"/g, '""');
          return `"${val}"`;
        }).join(",")
      )
    ].join("\r\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },

  downloadCsv(arg1, arg2) {
    this.downloadCSV(arg1, arg2);
  },

  parseCSV(text) {
    const lines = text.split(/\r?\n/).filter(line => line.trim().length > 0);
    if (!lines.length) return [];

    const parseLine = (line) => {
      const values = [];
      let inQuotes = false;
      let current = '';
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
          if (inQuotes && line[i + 1] === '"') {
            current += '"';
            i++; // skip escaped quote
          } else {
            inQuotes = !inQuotes;
          }
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim().replace(/^["']|["']$/g, ''));
          current = '';
        } else {
          current += char;
        }
      }
      values.push(current.trim().replace(/^["']|["']$/g, ''));
      return values;
    };

    const headers = parseLine(lines[0]);
    const records = [];

    for (let i = 1; i < lines.length; i++) {
      const values = parseLine(lines[i]);
      const obj = {};
      headers.forEach((header, idx) => {
        obj[header] = values[idx] !== undefined ? values[idx] : "";
      });
      records.push(obj);
    }
    return records;
  },

  importInstitutionsFromCSV(csvText) {
    const rows = this.parseCSV(csvText);
    let created = 0;
    let skipped = 0;
    let rejected = 0;
    const errors = [];

    rows.forEach((row, idx) => {
      const permId = row["Permanent ID"] || row["permanent_id"] || row["id"];
      const name = row["Institution Name"] || row["name"];
      const state = row["State"] || row["state"];
      const category = row["Category"] || row["category"] || "Engineering and Technology";
      const instType = row["Institution Type"] || row["institution_type"] || "Private-Self Financed";

      if (!permId || !name || !state) {
        rejected++;
        errors.push(`Row ${idx + 2}: Missing mandatory fields (Permanent ID, Name, State).`);
        return;
      }

      const existing = localStore.db.institutions.find(i => i.permanent_id === permId);
      if (existing) {
        skipped++;
        return;
      }

      const newInst = {
        id: "INST-" + Math.floor(10000 + Math.random() * 90000),
        name: name,
        permanent_id: permId,
        state: state,
        district: row["District"] || row["district"] || state,
        city: row["City"] || row["city"] || state,
        address: row["Address"] || row["address"] || "",
        category: category,
        institution_type: instType,
        affiliation: row["Affiliation"] || row["affiliation"] || "",
        website: row["Website"] || row["website"] || "",
        approval_status: row["Status"] || row["approval_status"] || "Approved",
        approval_period: row["Approval Period"] || row["approval_period"] || "2026-2027",
        programmes_count: parseInt(row["Programmes"] || row["programmes_count"]) || 0,
        total_intake: parseInt(row["Intake"] || row["total_intake"]) || 0,
        data_source: "CSV Import",
        verified_status: "Imported / Unverified",
        last_verified: new Date().toISOString().slice(0, 10)
      };

      localStore.db.institutions.push(newInst);
      created++;
    });

    if (created > 0) {
      localStore.log("Admin Officer", "Administrator", "Batch CSV Import", "Institution", `BATCH-${created}`, `Imported ${created} institutions, skipped ${skipped} duplicates.`);
      localStore.save();
    }

    return { total: rows.length, created, skipped, rejected, errors };
  }
};

if (typeof window !== "undefined") {
  window.CSVUtil = CSVUtil;
  window.CsvUtil = CSVUtil;
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = { CSVUtil, CsvUtil: CSVUtil };
}
