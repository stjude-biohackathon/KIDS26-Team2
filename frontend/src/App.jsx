import { useEffect, useState } from "react";
import Header from "./components/Header";
import QuestionForm from "./components/QuestionForm";
import AnswerCard from "./components/AnswerCard";

const defaultResult = {
  value: "2,134",
  label: "ICU patients",
  summary:
    "Among adult ICU stays, 2,134 patients were age 65 or older at admission. This estimate includes one record per patient and excludes pediatric admissions.",
  facts: [
    ["Age cutoff", "65+"],
    ["ICU stays", "7,442"],
    ["Share of cohort", "31.6%"],
  ],
  rows: [
    ["18-34", "412", "8.4%"],
    ["35-49", "631", "12.9%"],
    ["50-64", "1,335", "27.2%"],
    ["65-79", "1,407", "28.7%"],
    ["80+", "727", "14.8%"],
  ],
  sql: `SELECT
  COUNT(DISTINCT subject_id) AS patient_count
FROM mimiciv.icustays i
WHERE age >= 65;`,
};

function buildResult(question) {
  const normalized = question.toLowerCase();

  if (normalized.includes("average") || normalized.includes("stay")) {
    return {
      value: "4.8",
      label: "days average",
      summary:
        "Average ICU length of stay was 4.8 days across adult admissions, with longer stays most common in cardiothoracic and medical ICU populations.",
      facts: [
        ["Admissions", "9,812"],
        ["Median", "3.1 days"],
        ["Longest unit", "Cardiothoracic"],
      ],
      rows: [
        ["Medical", "5.1", "38%"],
        ["Surgical", "4.4", "31%"],
        ["Cardiothoracic", "6.2", "19%"],
        ["Neuro", "3.9", "12%"],
      ],
      sql: `SELECT
  AVG(los_icu) AS avg_icu_stay_days
FROM mimiciv.icustays;`,
    };
  }

  if (normalized.includes("diagnosis") || normalized.includes("common")) {
    return {
      value: "1,942",
      label: "admissions",
      summary:
        "Sepsis was the most frequent diagnosis category among ICU admissions, followed by respiratory failure and acute kidney injury.",
      facts: [
        ["Top diagnosis", "Sepsis"],
        ["Admissions", "1,942"],
        ["Share", "18.7%"],
      ],
      rows: [
        ["Sepsis", "1,942", "18.7%"],
        ["Respiratory failure", "1,511", "14.6%"],
        ["Acute kidney injury", "1,234", "11.9%"],
        ["Heart failure", "968", "9.3%"],
      ],
      sql: `SELECT
  diagnosis,
  COUNT(*) AS admission_count
FROM mimiciv.diagnoses_icd
GROUP BY diagnosis
ORDER BY admission_count DESC
LIMIT 4;`,
    };
  }

  return defaultResult;
}

export default function App() {
  const [conversation, setConversation] = useState([]);
  const [toast, setToast] = useState("");

  useEffect(() => {
    if (!toast) return undefined;

    const timeoutId = window.setTimeout(() => setToast(""), 1800);
    return () => window.clearTimeout(timeoutId);
  }, [toast]);

  function handleSubmit(question) {
    const nextEntry = {
      question,
      result: buildResult(question),
    };

    setConversation((previous) => [...previous, nextEntry]);
    setToast("Analysis ready");
  }

  function clearChat() {
    setConversation([]);
    setToast("Chat cleared");
  }

  return (
    <div className="app-shell">
      <Header />

      <main>
        {conversation.length === 0 ? (
          <QuestionForm onSubmit={handleSubmit} />
        ) : (
          <div className="chat-page">
            <div className="chat-heading">
              <div>
                <p className="eyebrow">Clinical query</p>
                <h2>Recent analysis</h2>
              </div>
              <button type="button" className="clear-chat" onClick={clearChat}>
                Clear chat
              </button>
            </div>

            <div className="conversation">
              {conversation.map((entry, index) => (
                <div className="chat-turn" key={`${entry.question}-${index}`}>
                  <div className="question-row">
                    <span className="avatar">You</span>
                    <p>{entry.question}</p>
                  </div>

                  <div className="assistant-label">
                    <span className="assistant-mark" aria-hidden="true">
                      <i />
                      <i />
                      <i />
                    </span>
                    Assistant
                  </div>

                  <AnswerCard result={entry.result} onToast={setToast} />
                </div>
              ))}
            </div>

            <QuestionForm compact onSubmit={handleSubmit} />
          </div>
        )}
      </main>

      <footer>
        <span>Privacy-safe data access</span>
        <span>Read-only query layer</span>
        <span>MIMIC-IV dataset</span>
      </footer>

      <div className={`toast ${toast ? "show" : ""}`}>{toast}</div>
    </div>
  );
}
