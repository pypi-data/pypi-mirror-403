# Anvil: Project Context & Manifesto

## 1. Project Identity
* **Name:** Anvil
* **Tagline:** Built by you. Managed by Anvil.
* **Core Mission:** To eliminate "Tool Rot" in the Agent Economy. We provide the infrastructure that keeps AI agents in production when APIs change, libraries update, and endpoints break.

## 2. The Strategic Pivot (B2B Infrastructure)
* **Old Strategy:** A tool-building SDK for agents (Creation).
* **New Strategy:** A "Reliability & Maintenance" Runtime (management).
* **The "Hair on Fire" Problem:** Companies spend 80% of their time maintaining agent tools due to "Software Entropy" (API deprecations, version conflicts). This is the "Maintenance Tax."
* **The Solution:** Anvil acts as a wrapper around agent tools. It detects runtime errors, auto-patches the code using an LLM, and persists the fix locally.

## 3. Core Philosophy: "Glass-Box Architecture"
* **Transparency:** Unlike "Black Box" cloud agents, Anvil saves every generated or patched tool to the local file system (e.g., `./anvil_tools/`).
* **Ownership:** The developer owns the code. They can audit, edit, commit, or eject Anvil entirely.
* **Security:** "Human-in-the-loop" options for production patches.

## 4. Key Technical Features
* **Just-In-Time (JIT) Generation:** Agents can generate tools on the fly if missing.
* **Self-Healing Runtime:**
    * Catches `ImportError`, `AttributeError`, `4xx/5xx` API errors.
    * Feeds stderr + source code to LLM.
    * Generates a patch -> Hot-reloads the module -> Retries execution.
* **The `@anvil.managed` Decorator:**
    * Allows developers to mark *manual* tools for Anvil supervision.
    * Example: A developer writes a complex scraper. If the CSS selectors change, Anvil detects the failure and updates the selector logic automatically.

## 5. Market Positioning (The "David Stevens" Defense)
* **Argument:** "Why build this if GPT-6 will just write perfect code?"
* **Defense:** Intelligence != Reliability.
    * Even if the model is perfect, the *environment* (APIs, auth, libraries) is chaotic.
    * Anvil is not a "better coder"; it is a **State Manager**. It provides the persistence, versioning, and audit trail that raw models lack.
    * Enterprises need a "Save Button" for agent capabilities, not just disposable inference.

## 6. Current Implementation Status
* **Language:** Python
* **Distribution:** PyPI (`pip install anvil-agents`)
* **Status:** Pivoting to "Managed Service" model.
* **Immediate Goal:** Validation of the "Maintenance Tax" pain point via a "Wizard of Oz" MVP.