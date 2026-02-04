import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
import SwiftUI

// Simple condition model
struct Condition: Identifiable {
    let id = UUID()
    let name: String
    let confidence: Double // 0.0 - 1.0
    let summary: String
}

final class QuickTriageModel: ObservableObject {
    @Published var symptomsText: String = ""
    @Published var age: Int = 30
    @Published var sex: String = "Prefer not"
    @Published var results: [Condition] = []
    @Published var isUrgent: Bool = false

    // Tiny symptom -> candidate map
    private let symptomMap: [String: [(String, String)]] = [
        "fever": [("Influenza", "Common viral infection causing fever and body aches."),
                  ("COVID-19", "May cause fever, cough, and fatigue.")],
        "cough": [("Common Cold", "Usually mild; cough, runny nose."),
                  ("Bronchitis", "Inflammation of airways; may produce wheeze or phlegm.")],
        "chest pain": [("Angina / Cardiac", "Could be heart-related — seek immediate care for severe pain."),
                       ("Reflux", "Acid reflux can mimic chest discomfort.")],
        "headache": [("Migraine", "Severe, throbbing, may have light sensitivity."),
                     ("Tension headache", "Often stress-related.")],
        "nausea": [("Gastroenteritis", "Stomach bug; nausea, sometimes vomiting.")],
        "shortness of breath": [("Asthma/Reactive airway", "Wheezing and breathlessness."),
                                ("Pneumonia", "Infection causing cough and breathing difficulty.")],
        "abdominal pain": [("Appendicitis", "Localized severe pain — seek care if severe."),
                           ("Gastritis", "Stomach inflammation causing pain.")]
    ]

    func diagnose() {
        let tokens = symptomsText
            .lowercased()
            .split { !$0.isLetter && !$0.isNumber }
            .map(String.init)
            .filter { !$0.isEmpty }

        var scores: [String: Double] = [:]
        var summaries: [String: String] = [:]

        for token in tokens {
            for (key, candidates) in symptomMap {
                if token.contains(key) || key.contains(token) || token == key {
                    for (name, summary) in candidates {
                        scores[name, default: 0.0] += 1.0
                        summaries[name] = summary
                    }
                }
            }
        }

        // If nothing matched, provide generic suggestions
        if scores.isEmpty {
            scores["Viral infection"] = 0.5
            summaries["Viral infection"] = "Symptoms may be viral; rest, fluids, and re-evaluate if worsening."
            scores["Non-specific symptoms"] = 0.3
            summaries["Non-specific symptoms"] = "Symptoms are non-specific; follow-up recommended."
        }

        // Normalize and create top 3 results
        let maxScore = scores.values.max() ?? 1.0
        let sorted = scores.sorted { $0.value > $1.value }.prefix(3)
        var conditions: [Condition] = []
        for (name, score) in sorted {
            // map 0..maxScore to 0.4..0.95
            let conf = min(0.95, 0.4 + (score / maxScore) * 0.55)
            conditions.append(Condition(name: name, confidence: conf, summary: summaries[name] ?? ""))
        }
        DispatchQueue.main.async {
            self.results = conditions
            self.isUrgent = checkUrgent(tokens: tokens)
        }
    }

    private func checkUrgent(tokens: [String]) -> Bool {
        let t = Set(tokens)
        // deterministic red-flag checks
        if t.contains("chest") && t.contains("pain") { return true }
        if t.contains("shortness") && t.contains("breath") { return true }
        if t.contains("faint") || t.contains("unconscious") { return true }
        // age-based example: older patients with breathlessness
        if age > 75 && (t.contains("breath") || t.contains("shortness")) { return true }
        return false
    }
}

struct ContentView: View {
    @StateObject private var model = QuickTriageModel()
    @State private var showingHelp = false

    var body: some View {
        ZStack {
            LinearGradient(colors: [Color(.systemBlue), Color(.systemTeal)], startPoint: .topLeading, endPoint: .bottomTrailing)
                .ignoresSafeArea()

            VStack(spacing: 20) {
                header
                formCard
                resultsArea
                Spacer(minLength: 10)
                footer
            }
            .padding()
            .foregroundColor(.white)
        }
        .sheet(isPresented: $showingHelp) {
            // Quick help sheet
            VStack {
                Text("Urgent — get help now")
                    .font(.title)
                    .bold()
                    .padding()
                Text("If you are experiencing chest pain, severe difficulty breathing, fainting, or sudden severe symptoms, call emergency services or visit the nearest hospital immediately.")
                    .padding()
                Button("Open Maps — Find Hospitals") {
                    if let url = URL(string: "maps://?q=hospital") {
                        UIApplication.shared.open(url)
                    }
                }
                .buttonStyle(.borderedProminent)
                .padding()
                Spacer()
            }
            .padding()
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("Quick Triage")
                    .font(.largeTitle).bold()
                Text("Enter symptoms and get quick possible causes")
                    .font(.subheadline)
                    .opacity(0.9)
            }
            Spacer()
            Circle()
                .fill(Color.white.opacity(0.2))
                .frame(width: 56, height: 56)
                .overlay(Image(systemName: "stethoscope").foregroundColor(.white))
        }
        .padding(.horizontal, 6)
    }

    private var formCard: some View {
        VStack(spacing: 12) {
            HStack {
                TextField("Enter symptoms (e.g. fever, cough, chest pain)", text: $model.symptomsText)
                    .textFieldStyle(.roundedBorder)
                    .padding(8)
                    .background(Color.white.opacity(0.15))
                    .cornerRadius(10)
            }
            HStack {
                Stepper("Age: \(model.age)", value: $model.age, in: 0...120)
                Spacer()
                Picker("", selection: $model.sex) {
                    Text("Prefer not").tag("Prefer not")
                    Text("Female").tag("Female")
                    Text("Male").tag("Male")
                    Text("Other").tag("Other")
                }
                .pickerStyle(MenuPickerStyle())
                .padding(.horizontal, 8)
                .background(Color.white.opacity(0.12))
                .cornerRadius(8)
            }
            HStack {
                Button(action: {
                    withAnimation { model.diagnose() }
                }) {
                    HStack {
                        Image(systemName: "bolt.fill")
                        Text("Diagnose")
                            .bold()
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color.white.opacity(0.18))
                    .cornerRadius(12)
                }
            }
        }
        .padding()
        .background(BlurView(style: .systemUltraThinMaterialDark))
        .cornerRadius(16)
        .shadow(radius: 8)
    }

    private var resultsArea: some View {
        VStack(alignment: .leading, spacing: 12) {
            if model.results.isEmpty {
                Text("No results yet. Enter symptoms and tap Diagnose.")
                    .foregroundColor(.white.opacity(0.9))
                    .padding(.top, 8)
            } else {
                HStack {
                    Text("Top possibilities")
                        .font(.headline)
                    Spacer()
                    if model.isUrgent {
                        Text("URGENT")
                            .font(.caption).bold()
                            .padding(6)
                            .background(Color.red)
                            .cornerRadius(8)
                    }
                }
                ForEach(model.results) { c in
                    HStack {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(c.name).bold()
                            Text(c.summary).font(.caption)
                                .foregroundColor(.white.opacity(0.9))
                        }
                        Spacer()
                        Text("\(Int(c.confidence * 100))%")
                            .font(.headline)
                    }
                    .padding()
                    .background(Color.white.opacity(0.08))
                    .cornerRadius(12)
                }
                if model.isUrgent {
                    Button(action: { showingHelp = true }) {
                        HStack {
                            Image(systemName: "phone.fill")
                            Text("Get urgent help")
                                .bold()
                        }
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.red.opacity(0.9))
                        .cornerRadius(12)
                    }
                    .padding(.top, 8)
                }
            }
        }
        .padding()
    }

    private var footer: some View {
        HStack {
            Text("Not a medical diagnosis. For emergency call local services.")
                .font(.footnote)
                .opacity(0.95)
            Spacer()
            Button(action: {
                // clear
                withAnimation {
                    model.symptomsText = ""
                    model.results = []
                    model.isUrgent = false
                }
            }) {
                Image(systemName: "trash")
            }
            .buttonStyle(.borderless)
        }
        .padding(.horizontal, 4)
    }
}

// Small blur helper (uses UIKit's UIVisualEffectView)
import UIKit
struct BlurView: UIViewRepresentable {
    let style: UIBlurEffect.Style
    func makeUIView(context: Context) -> UIVisualEffectView {
        UIVisualEffectView(effect: UIBlurEffect(style: style))
    }
    func updateUIView(_ uiView: UIVisualEffectView, context: Context) {}
}

import SwiftUI

struct SymptomEntryView: View {
    @EnvironmentObject var session: SymptomSession
    @State private var freeText = ""
    @State private var showingFollowUps = false

    let commonSymptoms = ["Fever","Cough","Chest pain","Headache","Nausea","Shortness of breath","Fatigue","Abdominal pain"]

    var body: some View {
        Form {
            Section("Your details") {
                HStack {
                    TextField("Age", text: $session.ageText)
                        .keyboardType(.numberPad)
                    Picker("Sex", selection: $session.sex) {
                        Text("Prefer not").tag("unknown")
                        Text("Female").tag("female")
                        Text("Male").tag("male")
                        Text("Other").tag("other")
                    }
                    .pickerStyle(.segmented)
                }
            }

            Section("Select symptoms") {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(commonSymptoms, id: \.self) { s in
                            Button(action: {
                                session.toggleSymptom(s)
                            }) {
                                Text(s)
                                    .padding(8)
                                    .background(session.symptoms.contains(s) ? Color.blue.opacity(0.8) : Color.gray.opacity(0.2))
                                    .foregroundColor(session.symptoms.contains(s) ? .white : .primary)
                                    .cornerRadius(10)
                            }
                        }
                    }.padding(.vertical, 4)
                }
                TextField("Other symptoms (comma separated)", text: $freeText)
                    .onSubmit {
                        session.addFreeTextSymptoms(freeText)
                        freeText = ""
                    }
            }

            Section {
                Button("Continue") {
                    session.addFreeTextSymptoms(freeText)
                    showingFollowUps = true
                }
                .disabled(session.symptoms.isEmpty && freeText.isEmpty)
            }
        }
        .navigationTitle("Enter symptoms")
        .navigationBarTitleDisplayMode(.inline)
        .background(
            NavigationLink("", destination: FollowUpQuestionView().environmentObject(session), isActive: $showingFollowUps)
        )
    }
}
