/**
 * Raqib Runbook UI — Alpine.js mixin.
 *
 * Provides (all bound to `this` = Alpine component):
 *   copiedIndex         — string | null, tracks which command was just copied
 *   copyAnnouncement    — string, ARIA live region text
 *   copyToClipboard()   — copies text, shows ✓ for 1.5s, announces to screen readers
 *   trackActionClick()  — fires /api/audit/action-url-click (fire-and-forget)
 *   trackRunbookView()  — fires /api/audit/runbook-view (fire-and-forget)
 *   severityClass()     — Tailwind classes for card border/bg
 *   severityBadgeClass()— Tailwind classes for severity pill
 *   severityLabel()     — uppercase ARIA-safe label
 *
 * Does NOT depend on Alpine.data() — works via object spread.
 * Usage in HTML:  x-data="{ ...runbookUI(), ...yourExistingData }"
 */

(function () {
    "use strict";

    function severityClass(sev) {
        switch (sev) {
            case "critical": return "border-red-500 bg-red-500/5";
            case "error":    return "border-amber-500 bg-amber-500/5";
            case "warn":     return "border-cyan-500 bg-cyan-500/5";
            default:         return "border-slate-500 bg-slate-500/5";
        }
    }

    function severityBadgeClass(sev) {
        switch (sev) {
            case "critical": return "bg-red-500/20 text-red-400";
            case "error":    return "bg-amber-500/20 text-amber-400";
            case "warn":     return "bg-cyan-500/20 text-cyan-400";
            default:         return "bg-slate-500/20 text-slate-300";
        }
    }

    function severityLabel(sev) {
        return (sev || "info").toUpperCase();
    }

    function runbookUI() {
        return {
            copiedIndex: null,
            copyAnnouncement: "",

            async copyToClipboard(text) {
                if (!text) return;

                const showSuccess = () => {
                    this.copiedIndex = text;
                    this.copyAnnouncement = "Copied to clipboard";
                    setTimeout(() => {
                        this.copiedIndex = null;
                        this.copyAnnouncement = "";
                    }, 1500);
                };

                if (navigator.clipboard && window.isSecureContext) {
                    try {
                        await navigator.clipboard.writeText(text);
                        showSuccess();
                        return;
                    } catch (_) {
                        /* fall through */
                    }
                }

                // Legacy fallback for non-HTTPS localhost / older browsers
                try {
                    const ta = document.createElement("textarea");
                    ta.value = text;
                    ta.style.position = "fixed";
                    ta.style.opacity = "0";
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand("copy");
                    document.body.removeChild(ta);
                    showSuccess();
                } catch (err) {
                    console.error("copy failed", err);
                }
            },

            trackActionClick(runbookId) {
                if (!runbookId) return;
                fetch("/api/audit/action-url-click", {
                    method: "POST",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ runbook_id: runbookId }),
                }).catch(() => {});
            },

            trackRunbookView(runbook) {
                if (!runbook) return;
                const id = runbook.id || runbook.title;
                fetch("/api/audit/runbook-view", {
                    method: "POST",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        runbook_id: id,
                        severity: runbook.severity,
                    }),
                }).catch(() => {});
            },

            severityClass,
            severityBadgeClass,
            severityLabel,
        };
    }

    window.runbookUI = runbookUI;

    document.addEventListener("alpine:init", () => {
        if (window.Alpine) window.Alpine.data("runbookUI", runbookUI);
    });
})();
