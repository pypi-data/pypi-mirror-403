"""
Tailwind CSS to Python CSS dictionary converter.

This module provides a comprehensive mapping of Tailwind CSS utility classes
to their CSS equivalents, enabling Tailwind-like styling in Python/Streamlit.

Supports:
- All standard Tailwind classes (~2100+)
- Opacity modifiers (bg-blue-500/50)
- Variant prefixes (hover:, focus:, active:)
"""

from typing import Dict, Tuple, Any, Union
import re

# =============================================================================
# TAILWIND COLOR PALETTE (Official Tailwind v3 colors)
# =============================================================================

COLORS: Dict[str, Dict[str, str]] = {
    "slate": {
        "50": "#f8fafc", "100": "#f1f5f9", "200": "#e2e8f0", "300": "#cbd5e1",
        "400": "#94a3b8", "500": "#64748b", "600": "#475569", "700": "#334155",
        "800": "#1e293b", "900": "#0f172a", "950": "#020617",
    },
    "gray": {
        "50": "#f9fafb", "100": "#f3f4f6", "200": "#e5e7eb", "300": "#d1d5db",
        "400": "#9ca3af", "500": "#6b7280", "600": "#4b5563", "700": "#374151",
        "800": "#1f2937", "900": "#111827", "950": "#030712",
    },
    "zinc": {
        "50": "#fafafa", "100": "#f4f4f5", "200": "#e4e4e7", "300": "#d4d4d8",
        "400": "#a1a1aa", "500": "#71717a", "600": "#52525b", "700": "#3f3f46",
        "800": "#27272a", "900": "#18181b", "950": "#09090b",
    },
    "neutral": {
        "50": "#fafafa", "100": "#f5f5f5", "200": "#e5e5e5", "300": "#d4d4d4",
        "400": "#a3a3a3", "500": "#737373", "600": "#525252", "700": "#404040",
        "800": "#262626", "900": "#171717", "950": "#0a0a0a",
    },
    "stone": {
        "50": "#fafaf9", "100": "#f5f5f4", "200": "#e7e5e4", "300": "#d6d3d1",
        "400": "#a8a29e", "500": "#78716c", "600": "#57534e", "700": "#44403c",
        "800": "#292524", "900": "#1c1917", "950": "#0c0a09",
    },
    "red": {
        "50": "#fef2f2", "100": "#fee2e2", "200": "#fecaca", "300": "#fca5a5",
        "400": "#f87171", "500": "#ef4444", "600": "#dc2626", "700": "#b91c1c",
        "800": "#991b1b", "900": "#7f1d1d", "950": "#450a0a",
    },
    "orange": {
        "50": "#fff7ed", "100": "#ffedd5", "200": "#fed7aa", "300": "#fdba74",
        "400": "#fb923c", "500": "#f97316", "600": "#ea580c", "700": "#c2410c",
        "800": "#9a3412", "900": "#7c2d12", "950": "#431407",
    },
    "amber": {
        "50": "#fffbeb", "100": "#fef3c7", "200": "#fde68a", "300": "#fcd34d",
        "400": "#fbbf24", "500": "#f59e0b", "600": "#d97706", "700": "#b45309",
        "800": "#92400e", "900": "#78350f", "950": "#451a03",
    },
    "yellow": {
        "50": "#fefce8", "100": "#fef9c3", "200": "#fef08a", "300": "#fde047",
        "400": "#facc15", "500": "#eab308", "600": "#ca8a04", "700": "#a16207",
        "800": "#854d0e", "900": "#713f12", "950": "#422006",
    },
    "lime": {
        "50": "#f7fee7", "100": "#ecfccb", "200": "#d9f99d", "300": "#bef264",
        "400": "#a3e635", "500": "#84cc16", "600": "#65a30d", "700": "#4d7c0f",
        "800": "#3f6212", "900": "#365314", "950": "#1a2e05",
    },
    "green": {
        "50": "#f0fdf4", "100": "#dcfce7", "200": "#bbf7d0", "300": "#86efac",
        "400": "#4ade80", "500": "#22c55e", "600": "#16a34a", "700": "#15803d",
        "800": "#166534", "900": "#14532d", "950": "#052e16",
    },
    "emerald": {
        "50": "#ecfdf5", "100": "#d1fae5", "200": "#a7f3d0", "300": "#6ee7b7",
        "400": "#34d399", "500": "#10b981", "600": "#059669", "700": "#047857",
        "800": "#065f46", "900": "#064e3b", "950": "#022c22",
    },
    "teal": {
        "50": "#f0fdfa", "100": "#ccfbf1", "200": "#99f6e4", "300": "#5eead4",
        "400": "#2dd4bf", "500": "#14b8a6", "600": "#0d9488", "700": "#0f766e",
        "800": "#115e59", "900": "#134e4a", "950": "#042f2e",
    },
    "cyan": {
        "50": "#ecfeff", "100": "#cffafe", "200": "#a5f3fc", "300": "#67e8f9",
        "400": "#22d3ee", "500": "#06b6d4", "600": "#0891b2", "700": "#0e7490",
        "800": "#155e75", "900": "#164e63", "950": "#083344",
    },
    "sky": {
        "50": "#f0f9ff", "100": "#e0f2fe", "200": "#bae6fd", "300": "#7dd3fc",
        "400": "#38bdf8", "500": "#0ea5e9", "600": "#0284c7", "700": "#0369a1",
        "800": "#075985", "900": "#0c4a6e", "950": "#082f49",
    },
    "blue": {
        "50": "#eff6ff", "100": "#dbeafe", "200": "#bfdbfe", "300": "#93c5fd",
        "400": "#60a5fa", "500": "#3b82f6", "600": "#2563eb", "700": "#1d4ed8",
        "800": "#1e40af", "900": "#1e3a8a", "950": "#172554",
    },
    "indigo": {
        "50": "#eef2ff", "100": "#e0e7ff", "200": "#c7d2fe", "300": "#a5b4fc",
        "400": "#818cf8", "500": "#6366f1", "600": "#4f46e5", "700": "#4338ca",
        "800": "#3730a3", "900": "#312e81", "950": "#1e1b4b",
    },
    "violet": {
        "50": "#f5f3ff", "100": "#ede9fe", "200": "#ddd6fe", "300": "#c4b5fd",
        "400": "#a78bfa", "500": "#8b5cf6", "600": "#7c3aed", "700": "#6d28d9",
        "800": "#5b21b6", "900": "#4c1d95", "950": "#2e1065",
    },
    "purple": {
        "50": "#faf5ff", "100": "#f3e8ff", "200": "#e9d5ff", "300": "#d8b4fe",
        "400": "#c084fc", "500": "#a855f7", "600": "#9333ea", "700": "#7e22ce",
        "800": "#6b21a8", "900": "#581c87", "950": "#3b0764",
    },
    "fuchsia": {
        "50": "#fdf4ff", "100": "#fae8ff", "200": "#f5d0fe", "300": "#f0abfc",
        "400": "#e879f9", "500": "#d946ef", "600": "#c026d3", "700": "#a21caf",
        "800": "#86198f", "900": "#701a75", "950": "#4a044e",
    },
    "pink": {
        "50": "#fdf2f8", "100": "#fce7f3", "200": "#fbcfe8", "300": "#f9a8d4",
        "400": "#f472b6", "500": "#ec4899", "600": "#db2777", "700": "#be185d",
        "800": "#9d174d", "900": "#831843", "950": "#500724",
    },
    "rose": {
        "50": "#fff1f2", "100": "#ffe4e6", "200": "#fecdd3", "300": "#fda4af",
        "400": "#fb7185", "500": "#f43f5e", "600": "#e11d48", "700": "#be123c",
        "800": "#9f1239", "900": "#881337", "950": "#4c0519",
    },
}

# Special colors
SPECIAL_COLORS: Dict[str, str] = {
    "black": "#000000",
    "white": "#ffffff",
    "transparent": "transparent",
    "current": "currentColor",
    "inherit": "inherit",
}

# =============================================================================
# SPACING SCALE
# =============================================================================

SPACING: Dict[str, str] = {
    "0": "0px",
    "px": "1px",
    "0.5": "0.125rem",
    "1": "0.25rem",
    "1.5": "0.375rem",
    "2": "0.5rem",
    "2.5": "0.625rem",
    "3": "0.75rem",
    "3.5": "0.875rem",
    "4": "1rem",
    "5": "1.25rem",
    "6": "1.5rem",
    "7": "1.75rem",
    "8": "2rem",
    "9": "2.25rem",
    "10": "2.5rem",
    "11": "2.75rem",
    "12": "3rem",
    "14": "3.5rem",
    "16": "4rem",
    "20": "5rem",
    "24": "6rem",
    "28": "7rem",
    "32": "8rem",
    "36": "9rem",
    "40": "10rem",
    "44": "11rem",
    "48": "12rem",
    "52": "13rem",
    "56": "14rem",
    "60": "15rem",
    "64": "16rem",
    "72": "18rem",
    "80": "20rem",
    "96": "24rem",
}

# =============================================================================
# STATIC MAPPINGS
# =============================================================================

# Typography
FONT_SIZE: Dict[str, Dict[str, str]] = {
    "text-xs": {"font-size": "0.75rem", "line-height": "1rem"},
    "text-sm": {"font-size": "0.875rem", "line-height": "1.25rem"},
    "text-base": {"font-size": "1rem", "line-height": "1.5rem"},
    "text-lg": {"font-size": "1.125rem", "line-height": "1.75rem"},
    "text-xl": {"font-size": "1.25rem", "line-height": "1.75rem"},
    "text-2xl": {"font-size": "1.5rem", "line-height": "2rem"},
    "text-3xl": {"font-size": "1.875rem", "line-height": "2.25rem"},
    "text-4xl": {"font-size": "2.25rem", "line-height": "2.5rem"},
    "text-5xl": {"font-size": "3rem", "line-height": "1"},
    "text-6xl": {"font-size": "3.75rem", "line-height": "1"},
    "text-7xl": {"font-size": "4.5rem", "line-height": "1"},
    "text-8xl": {"font-size": "6rem", "line-height": "1"},
    "text-9xl": {"font-size": "8rem", "line-height": "1"},
}

FONT_WEIGHT: Dict[str, str] = {
    "font-thin": "100",
    "font-extralight": "200",
    "font-light": "300",
    "font-normal": "400",
    "font-medium": "500",
    "font-semibold": "600",
    "font-bold": "700",
    "font-extrabold": "800",
    "font-black": "900",
}

LINE_HEIGHT: Dict[str, str] = {
    "leading-none": "1",
    "leading-tight": "1.25",
    "leading-snug": "1.375",
    "leading-normal": "1.5",
    "leading-relaxed": "1.625",
    "leading-loose": "2",
    "leading-3": "0.75rem",
    "leading-4": "1rem",
    "leading-5": "1.25rem",
    "leading-6": "1.5rem",
    "leading-7": "1.75rem",
    "leading-8": "2rem",
    "leading-9": "2.25rem",
    "leading-10": "2.5rem",
}

LETTER_SPACING: Dict[str, str] = {
    "tracking-tighter": "-0.05em",
    "tracking-tight": "-0.025em",
    "tracking-normal": "0em",
    "tracking-wide": "0.025em",
    "tracking-wider": "0.05em",
    "tracking-widest": "0.1em",
}

TEXT_ALIGN: Dict[str, str] = {
    "text-left": "left",
    "text-center": "center",
    "text-right": "right",
    "text-justify": "justify",
    "text-start": "start",
    "text-end": "end",
}

TEXT_TRANSFORM: Dict[str, str] = {
    "uppercase": "uppercase",
    "lowercase": "lowercase",
    "capitalize": "capitalize",
    "normal-case": "none",
}

TEXT_DECORATION: Dict[str, str] = {
    "underline": "underline",
    "overline": "overline",
    "line-through": "line-through",
    "no-underline": "none",
}

TEXT_OVERFLOW: Dict[str, Dict[str, str]] = {
    "truncate": {
        "overflow": "hidden",
        "text-overflow": "ellipsis",
        "white-space": "nowrap",
    },
    "text-ellipsis": {"text-overflow": "ellipsis"},
    "text-clip": {"text-overflow": "clip"},
}

WHITESPACE: Dict[str, str] = {
    "whitespace-normal": "normal",
    "whitespace-nowrap": "nowrap",
    "whitespace-pre": "pre",
    "whitespace-pre-line": "pre-line",
    "whitespace-pre-wrap": "pre-wrap",
    "whitespace-break-spaces": "break-spaces",
}

WORD_BREAK: Dict[str, Dict[str, str]] = {
    "break-normal": {"overflow-wrap": "normal", "word-break": "normal"},
    "break-words": {"overflow-wrap": "break-word"},
    "break-all": {"word-break": "break-all"},
    "break-keep": {"word-break": "keep-all"},
}

# Border radius
BORDER_RADIUS: Dict[str, str] = {
    "rounded-none": "0px",
    "rounded-sm": "0.125rem",
    "rounded": "0.25rem",
    "rounded-md": "0.375rem",
    "rounded-lg": "0.5rem",
    "rounded-xl": "0.75rem",
    "rounded-2xl": "1rem",
    "rounded-3xl": "1.5rem",
    "rounded-full": "9999px",
}

BORDER_WIDTH: Dict[str, str] = {
    "border": "1px",
    "border-0": "0px",
    "border-2": "2px",
    "border-4": "4px",
    "border-8": "8px",
}

BORDER_STYLE: Dict[str, str] = {
    "border-solid": "solid",
    "border-dashed": "dashed",
    "border-dotted": "dotted",
    "border-double": "double",
    "border-hidden": "hidden",
    "border-none": "none",
}

# Layout
DISPLAY: Dict[str, str] = {
    "block": "block",
    "inline-block": "inline-block",
    "inline": "inline",
    "flex": "flex",
    "inline-flex": "inline-flex",
    "table": "table",
    "inline-table": "inline-table",
    "table-caption": "table-caption",
    "table-cell": "table-cell",
    "table-column": "table-column",
    "table-column-group": "table-column-group",
    "table-footer-group": "table-footer-group",
    "table-header-group": "table-header-group",
    "table-row-group": "table-row-group",
    "table-row": "table-row",
    "flow-root": "flow-root",
    "grid": "grid",
    "inline-grid": "inline-grid",
    "contents": "contents",
    "list-item": "list-item",
    "hidden": "none",
}

FLEX_DIRECTION: Dict[str, str] = {
    "flex-row": "row",
    "flex-row-reverse": "row-reverse",
    "flex-col": "column",
    "flex-col-reverse": "column-reverse",
}

FLEX_WRAP: Dict[str, str] = {
    "flex-wrap": "wrap",
    "flex-wrap-reverse": "wrap-reverse",
    "flex-nowrap": "nowrap",
}

FLEX: Dict[str, str] = {
    "flex-1": "1 1 0%",
    "flex-auto": "1 1 auto",
    "flex-initial": "0 1 auto",
    "flex-none": "none",
}

FLEX_GROW: Dict[str, str] = {
    "grow": "1",
    "grow-0": "0",
}

FLEX_SHRINK: Dict[str, str] = {
    "shrink": "1",
    "shrink-0": "0",
}

JUSTIFY_CONTENT: Dict[str, str] = {
    "justify-normal": "normal",
    "justify-start": "flex-start",
    "justify-end": "flex-end",
    "justify-center": "center",
    "justify-between": "space-between",
    "justify-around": "space-around",
    "justify-evenly": "space-evenly",
    "justify-stretch": "stretch",
}

ALIGN_ITEMS: Dict[str, str] = {
    "items-start": "flex-start",
    "items-end": "flex-end",
    "items-center": "center",
    "items-baseline": "baseline",
    "items-stretch": "stretch",
}

ALIGN_SELF: Dict[str, str] = {
    "self-auto": "auto",
    "self-start": "flex-start",
    "self-end": "flex-end",
    "self-center": "center",
    "self-stretch": "stretch",
    "self-baseline": "baseline",
}

ALIGN_CONTENT: Dict[str, str] = {
    "content-normal": "normal",
    "content-center": "center",
    "content-start": "flex-start",
    "content-end": "flex-end",
    "content-between": "space-between",
    "content-around": "space-around",
    "content-evenly": "space-evenly",
    "content-baseline": "baseline",
    "content-stretch": "stretch",
}

# Positioning
POSITION: Dict[str, str] = {
    "static": "static",
    "fixed": "fixed",
    "absolute": "absolute",
    "relative": "relative",
    "sticky": "sticky",
}

Z_INDEX: Dict[str, str] = {
    "z-0": "0",
    "z-10": "10",
    "z-20": "20",
    "z-30": "30",
    "z-40": "40",
    "z-50": "50",
    "z-auto": "auto",
}

# Sizing
WIDTH_SPECIAL: Dict[str, str] = {
    "w-auto": "auto",
    "w-full": "100%",
    "w-screen": "100vw",
    "w-svw": "100svw",
    "w-lvw": "100lvw",
    "w-dvw": "100dvw",
    "w-min": "min-content",
    "w-max": "max-content",
    "w-fit": "fit-content",
}

HEIGHT_SPECIAL: Dict[str, str] = {
    "h-auto": "auto",
    "h-full": "100%",
    "h-screen": "100vh",
    "h-svh": "100svh",
    "h-lvh": "100lvh",
    "h-dvh": "100dvh",
    "h-min": "min-content",
    "h-max": "max-content",
    "h-fit": "fit-content",
}

MIN_WIDTH: Dict[str, str] = {
    "min-w-0": "0px",
    "min-w-full": "100%",
    "min-w-min": "min-content",
    "min-w-max": "max-content",
    "min-w-fit": "fit-content",
}

MAX_WIDTH: Dict[str, str] = {
    "max-w-0": "0rem",
    "max-w-none": "none",
    "max-w-xs": "20rem",
    "max-w-sm": "24rem",
    "max-w-md": "28rem",
    "max-w-lg": "32rem",
    "max-w-xl": "36rem",
    "max-w-2xl": "42rem",
    "max-w-3xl": "48rem",
    "max-w-4xl": "56rem",
    "max-w-5xl": "64rem",
    "max-w-6xl": "72rem",
    "max-w-7xl": "80rem",
    "max-w-full": "100%",
    "max-w-min": "min-content",
    "max-w-max": "max-content",
    "max-w-fit": "fit-content",
    "max-w-prose": "65ch",
    "max-w-screen-sm": "640px",
    "max-w-screen-md": "768px",
    "max-w-screen-lg": "1024px",
    "max-w-screen-xl": "1280px",
    "max-w-screen-2xl": "1536px",
}

MIN_HEIGHT: Dict[str, str] = {
    "min-h-0": "0px",
    "min-h-full": "100%",
    "min-h-screen": "100vh",
    "min-h-svh": "100svh",
    "min-h-lvh": "100lvh",
    "min-h-dvh": "100dvh",
    "min-h-min": "min-content",
    "min-h-max": "max-content",
    "min-h-fit": "fit-content",
}

MAX_HEIGHT: Dict[str, str] = {
    "max-h-none": "none",
    "max-h-full": "100%",
    "max-h-screen": "100vh",
    "max-h-svh": "100svh",
    "max-h-lvh": "100lvh",
    "max-h-dvh": "100dvh",
    "max-h-min": "min-content",
    "max-h-max": "max-content",
    "max-h-fit": "fit-content",
}

# Fraction widths
WIDTH_FRACTIONS: Dict[str, str] = {
    "w-1/2": "50%",
    "w-1/3": "33.333333%",
    "w-2/3": "66.666667%",
    "w-1/4": "25%",
    "w-2/4": "50%",
    "w-3/4": "75%",
    "w-1/5": "20%",
    "w-2/5": "40%",
    "w-3/5": "60%",
    "w-4/5": "80%",
    "w-1/6": "16.666667%",
    "w-2/6": "33.333333%",
    "w-3/6": "50%",
    "w-4/6": "66.666667%",
    "w-5/6": "83.333333%",
    "w-1/12": "8.333333%",
    "w-2/12": "16.666667%",
    "w-3/12": "25%",
    "w-4/12": "33.333333%",
    "w-5/12": "41.666667%",
    "w-6/12": "50%",
    "w-7/12": "58.333333%",
    "w-8/12": "66.666667%",
    "w-9/12": "75%",
    "w-10/12": "83.333333%",
    "w-11/12": "91.666667%",
}

HEIGHT_FRACTIONS: Dict[str, str] = {
    "h-1/2": "50%",
    "h-1/3": "33.333333%",
    "h-2/3": "66.666667%",
    "h-1/4": "25%",
    "h-2/4": "50%",
    "h-3/4": "75%",
    "h-1/5": "20%",
    "h-2/5": "40%",
    "h-3/5": "60%",
    "h-4/5": "80%",
    "h-1/6": "16.666667%",
    "h-2/6": "33.333333%",
    "h-3/6": "50%",
    "h-4/6": "66.666667%",
    "h-5/6": "83.333333%",
}

# Effects
SHADOW: Dict[str, str] = {
    "shadow-sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "shadow": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
    "shadow-md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    "shadow-lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    "shadow-xl": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
    "shadow-2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
    "shadow-inner": "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",
    "shadow-none": "0 0 #0000",
}

OPACITY: Dict[str, str] = {
    "opacity-0": "0",
    "opacity-5": "0.05",
    "opacity-10": "0.1",
    "opacity-15": "0.15",
    "opacity-20": "0.2",
    "opacity-25": "0.25",
    "opacity-30": "0.3",
    "opacity-35": "0.35",
    "opacity-40": "0.4",
    "opacity-45": "0.45",
    "opacity-50": "0.5",
    "opacity-55": "0.55",
    "opacity-60": "0.6",
    "opacity-65": "0.65",
    "opacity-70": "0.7",
    "opacity-75": "0.75",
    "opacity-80": "0.8",
    "opacity-85": "0.85",
    "opacity-90": "0.9",
    "opacity-95": "0.95",
    "opacity-100": "1",
}

BLUR: Dict[str, str] = {
    "blur-none": "blur(0)",
    "blur-sm": "blur(4px)",
    "blur": "blur(8px)",
    "blur-md": "blur(12px)",
    "blur-lg": "blur(16px)",
    "blur-xl": "blur(24px)",
    "blur-2xl": "blur(40px)",
    "blur-3xl": "blur(64px)",
}

# Backgrounds
BG_GRADIENT: Dict[str, str] = {
    "bg-gradient-to-t": "linear-gradient(to top, var(--tw-gradient-stops))",
    "bg-gradient-to-tr": "linear-gradient(to top right, var(--tw-gradient-stops))",
    "bg-gradient-to-r": "linear-gradient(to right, var(--tw-gradient-stops))",
    "bg-gradient-to-br": "linear-gradient(to bottom right, var(--tw-gradient-stops))",
    "bg-gradient-to-b": "linear-gradient(to bottom, var(--tw-gradient-stops))",
    "bg-gradient-to-bl": "linear-gradient(to bottom left, var(--tw-gradient-stops))",
    "bg-gradient-to-l": "linear-gradient(to left, var(--tw-gradient-stops))",
    "bg-gradient-to-tl": "linear-gradient(to top left, var(--tw-gradient-stops))",
}

BG_SIZE: Dict[str, str] = {
    "bg-auto": "auto",
    "bg-cover": "cover",
    "bg-contain": "contain",
}

BG_POSITION: Dict[str, str] = {
    "bg-bottom": "bottom",
    "bg-center": "center",
    "bg-left": "left",
    "bg-left-bottom": "left bottom",
    "bg-left-top": "left top",
    "bg-right": "right",
    "bg-right-bottom": "right bottom",
    "bg-right-top": "right top",
    "bg-top": "top",
}

BG_REPEAT: Dict[str, str] = {
    "bg-repeat": "repeat",
    "bg-no-repeat": "no-repeat",
    "bg-repeat-x": "repeat-x",
    "bg-repeat-y": "repeat-y",
    "bg-repeat-round": "round",
    "bg-repeat-space": "space",
}

# Overflow
OVERFLOW: Dict[str, str] = {
    "overflow-auto": "auto",
    "overflow-hidden": "hidden",
    "overflow-clip": "clip",
    "overflow-visible": "visible",
    "overflow-scroll": "scroll",
    "overflow-x-auto": "auto",
    "overflow-y-auto": "auto",
    "overflow-x-hidden": "hidden",
    "overflow-y-hidden": "hidden",
    "overflow-x-clip": "clip",
    "overflow-y-clip": "clip",
    "overflow-x-visible": "visible",
    "overflow-y-visible": "visible",
    "overflow-x-scroll": "scroll",
    "overflow-y-scroll": "scroll",
}

# Transitions
TRANSITION: Dict[str, Dict[str, str]] = {
    "transition-none": {"transition-property": "none"},
    "transition-all": {
        "transition-property": "all",
        "transition-timing-function": "cubic-bezier(0.4, 0, 0.2, 1)",
        "transition-duration": "150ms",
    },
    "transition": {
        "transition-property": "color, background-color, border-color, text-decoration-color, fill, stroke, opacity, box-shadow, transform, filter, backdrop-filter",
        "transition-timing-function": "cubic-bezier(0.4, 0, 0.2, 1)",
        "transition-duration": "150ms",
    },
    "transition-colors": {
        "transition-property": "color, background-color, border-color, text-decoration-color, fill, stroke",
        "transition-timing-function": "cubic-bezier(0.4, 0, 0.2, 1)",
        "transition-duration": "150ms",
    },
    "transition-opacity": {
        "transition-property": "opacity",
        "transition-timing-function": "cubic-bezier(0.4, 0, 0.2, 1)",
        "transition-duration": "150ms",
    },
    "transition-shadow": {
        "transition-property": "box-shadow",
        "transition-timing-function": "cubic-bezier(0.4, 0, 0.2, 1)",
        "transition-duration": "150ms",
    },
    "transition-transform": {
        "transition-property": "transform",
        "transition-timing-function": "cubic-bezier(0.4, 0, 0.2, 1)",
        "transition-duration": "150ms",
    },
}

DURATION: Dict[str, str] = {
    "duration-0": "0s",
    "duration-75": "75ms",
    "duration-100": "100ms",
    "duration-150": "150ms",
    "duration-200": "200ms",
    "duration-300": "300ms",
    "duration-500": "500ms",
    "duration-700": "700ms",
    "duration-1000": "1000ms",
}

TIMING_FUNCTION: Dict[str, str] = {
    "ease-linear": "linear",
    "ease-in": "cubic-bezier(0.4, 0, 1, 1)",
    "ease-out": "cubic-bezier(0, 0, 0.2, 1)",
    "ease-in-out": "cubic-bezier(0.4, 0, 0.2, 1)",
}

DELAY: Dict[str, str] = {
    "delay-0": "0s",
    "delay-75": "75ms",
    "delay-100": "100ms",
    "delay-150": "150ms",
    "delay-200": "200ms",
    "delay-300": "300ms",
    "delay-500": "500ms",
    "delay-700": "700ms",
    "delay-1000": "1000ms",
}

# Interactivity
CURSOR: Dict[str, str] = {
    "cursor-auto": "auto",
    "cursor-default": "default",
    "cursor-pointer": "pointer",
    "cursor-wait": "wait",
    "cursor-text": "text",
    "cursor-move": "move",
    "cursor-help": "help",
    "cursor-not-allowed": "not-allowed",
    "cursor-none": "none",
    "cursor-context-menu": "context-menu",
    "cursor-progress": "progress",
    "cursor-cell": "cell",
    "cursor-crosshair": "crosshair",
    "cursor-vertical-text": "vertical-text",
    "cursor-alias": "alias",
    "cursor-copy": "copy",
    "cursor-no-drop": "no-drop",
    "cursor-grab": "grab",
    "cursor-grabbing": "grabbing",
    "cursor-all-scroll": "all-scroll",
    "cursor-col-resize": "col-resize",
    "cursor-row-resize": "row-resize",
    "cursor-n-resize": "n-resize",
    "cursor-e-resize": "e-resize",
    "cursor-s-resize": "s-resize",
    "cursor-w-resize": "w-resize",
    "cursor-ne-resize": "ne-resize",
    "cursor-nw-resize": "nw-resize",
    "cursor-se-resize": "se-resize",
    "cursor-sw-resize": "sw-resize",
    "cursor-ew-resize": "ew-resize",
    "cursor-ns-resize": "ns-resize",
    "cursor-nesw-resize": "nesw-resize",
    "cursor-nwse-resize": "nwse-resize",
    "cursor-zoom-in": "zoom-in",
    "cursor-zoom-out": "zoom-out",
}

USER_SELECT: Dict[str, str] = {
    "select-none": "none",
    "select-text": "text",
    "select-all": "all",
    "select-auto": "auto",
}

POINTER_EVENTS: Dict[str, str] = {
    "pointer-events-none": "none",
    "pointer-events-auto": "auto",
}

# Object fit/position
OBJECT_FIT: Dict[str, str] = {
    "object-contain": "contain",
    "object-cover": "cover",
    "object-fill": "fill",
    "object-none": "none",
    "object-scale-down": "scale-down",
}

OBJECT_POSITION: Dict[str, str] = {
    "object-bottom": "bottom",
    "object-center": "center",
    "object-left": "left",
    "object-left-bottom": "left bottom",
    "object-left-top": "left top",
    "object-right": "right",
    "object-right-bottom": "right bottom",
    "object-right-top": "right top",
    "object-top": "top",
}

# Visibility
VISIBILITY: Dict[str, str] = {
    "visible": "visible",
    "invisible": "hidden",
    "collapse": "collapse",
}

# Box sizing
BOX_SIZING: Dict[str, str] = {
    "box-border": "border-box",
    "box-content": "content-box",
}

# Aspect ratio
ASPECT_RATIO: Dict[str, str] = {
    "aspect-auto": "auto",
    "aspect-square": "1 / 1",
    "aspect-video": "16 / 9",
}

# Grid
GRID_TEMPLATE_COLUMNS: Dict[str, str] = {
    "grid-cols-1": "repeat(1, minmax(0, 1fr))",
    "grid-cols-2": "repeat(2, minmax(0, 1fr))",
    "grid-cols-3": "repeat(3, minmax(0, 1fr))",
    "grid-cols-4": "repeat(4, minmax(0, 1fr))",
    "grid-cols-5": "repeat(5, minmax(0, 1fr))",
    "grid-cols-6": "repeat(6, minmax(0, 1fr))",
    "grid-cols-7": "repeat(7, minmax(0, 1fr))",
    "grid-cols-8": "repeat(8, minmax(0, 1fr))",
    "grid-cols-9": "repeat(9, minmax(0, 1fr))",
    "grid-cols-10": "repeat(10, minmax(0, 1fr))",
    "grid-cols-11": "repeat(11, minmax(0, 1fr))",
    "grid-cols-12": "repeat(12, minmax(0, 1fr))",
    "grid-cols-none": "none",
    "grid-cols-subgrid": "subgrid",
}

GRID_TEMPLATE_ROWS: Dict[str, str] = {
    "grid-rows-1": "repeat(1, minmax(0, 1fr))",
    "grid-rows-2": "repeat(2, minmax(0, 1fr))",
    "grid-rows-3": "repeat(3, minmax(0, 1fr))",
    "grid-rows-4": "repeat(4, minmax(0, 1fr))",
    "grid-rows-5": "repeat(5, minmax(0, 1fr))",
    "grid-rows-6": "repeat(6, minmax(0, 1fr))",
    "grid-rows-none": "none",
    "grid-rows-subgrid": "subgrid",
}

GRID_COLUMN: Dict[str, str] = {
    "col-auto": "auto",
    "col-span-1": "span 1 / span 1",
    "col-span-2": "span 2 / span 2",
    "col-span-3": "span 3 / span 3",
    "col-span-4": "span 4 / span 4",
    "col-span-5": "span 5 / span 5",
    "col-span-6": "span 6 / span 6",
    "col-span-7": "span 7 / span 7",
    "col-span-8": "span 8 / span 8",
    "col-span-9": "span 9 / span 9",
    "col-span-10": "span 10 / span 10",
    "col-span-11": "span 11 / span 11",
    "col-span-12": "span 12 / span 12",
    "col-span-full": "1 / -1",
}

GRID_ROW: Dict[str, str] = {
    "row-auto": "auto",
    "row-span-1": "span 1 / span 1",
    "row-span-2": "span 2 / span 2",
    "row-span-3": "span 3 / span 3",
    "row-span-4": "span 4 / span 4",
    "row-span-5": "span 5 / span 5",
    "row-span-6": "span 6 / span 6",
    "row-span-full": "1 / -1",
}

GRID_AUTO_FLOW: Dict[str, str] = {
    "grid-flow-row": "row",
    "grid-flow-col": "column",
    "grid-flow-dense": "dense",
    "grid-flow-row-dense": "row dense",
    "grid-flow-col-dense": "column dense",
}

GRID_AUTO_COLUMNS: Dict[str, str] = {
    "auto-cols-auto": "auto",
    "auto-cols-min": "min-content",
    "auto-cols-max": "max-content",
    "auto-cols-fr": "minmax(0, 1fr)",
}

GRID_AUTO_ROWS: Dict[str, str] = {
    "auto-rows-auto": "auto",
    "auto-rows-min": "min-content",
    "auto-rows-max": "max-content",
    "auto-rows-fr": "minmax(0, 1fr)",
}

PLACE_CONTENT: Dict[str, str] = {
    "place-content-center": "center",
    "place-content-start": "start",
    "place-content-end": "end",
    "place-content-between": "space-between",
    "place-content-around": "space-around",
    "place-content-evenly": "space-evenly",
    "place-content-baseline": "baseline",
    "place-content-stretch": "stretch",
}

PLACE_ITEMS: Dict[str, str] = {
    "place-items-start": "start",
    "place-items-end": "end",
    "place-items-center": "center",
    "place-items-baseline": "baseline",
    "place-items-stretch": "stretch",
}

PLACE_SELF: Dict[str, str] = {
    "place-self-auto": "auto",
    "place-self-start": "start",
    "place-self-end": "end",
    "place-self-center": "center",
    "place-self-stretch": "stretch",
}

# Ring (outline-like)
RING_WIDTH: Dict[str, Dict[str, str]] = {
    "ring-0": {"box-shadow": "var(--tw-ring-inset) 0 0 0 0px var(--tw-ring-color)"},
    "ring-1": {"box-shadow": "var(--tw-ring-inset) 0 0 0 1px var(--tw-ring-color)"},
    "ring-2": {"box-shadow": "var(--tw-ring-inset) 0 0 0 2px var(--tw-ring-color)"},
    "ring": {"box-shadow": "var(--tw-ring-inset) 0 0 0 3px var(--tw-ring-color)"},
    "ring-4": {"box-shadow": "var(--tw-ring-inset) 0 0 0 4px var(--tw-ring-color)"},
    "ring-8": {"box-shadow": "var(--tw-ring-inset) 0 0 0 8px var(--tw-ring-color)"},
    "ring-inset": {"--tw-ring-inset": "inset"},
}

OUTLINE_STYLE: Dict[str, Dict[str, str]] = {
    "outline-none": {"outline": "2px solid transparent", "outline-offset": "2px"},
    "outline": {"outline-style": "solid"},
    "outline-dashed": {"outline-style": "dashed"},
    "outline-dotted": {"outline-style": "dotted"},
    "outline-double": {"outline-style": "double"},
}

OUTLINE_WIDTH: Dict[str, str] = {
    "outline-0": "0px",
    "outline-1": "1px",
    "outline-2": "2px",
    "outline-4": "4px",
    "outline-8": "8px",
}

OUTLINE_OFFSET: Dict[str, str] = {
    "outline-offset-0": "0px",
    "outline-offset-1": "1px",
    "outline-offset-2": "2px",
    "outline-offset-4": "4px",
    "outline-offset-8": "8px",
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def hex_to_rgba(hex_color: str, opacity: float) -> str:
    """Convert hex color to rgba string.

    Args:
        hex_color: Hex color string (e.g., "#3b82f6")
        opacity: Opacity value from 0-100

    Returns:
        RGBA string (e.g., "rgba(59, 130, 246, 0.5)")
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {opacity / 100})"


def get_color(color_name: str, shade: str = None) -> str:
    """Get hex color from color name and optional shade.

    Args:
        color_name: Color name (e.g., "blue", "slate", "white")
        shade: Optional shade (e.g., "500", "900")

    Returns:
        Hex color string or special color value
    """
    if color_name in SPECIAL_COLORS:
        return SPECIAL_COLORS[color_name]

    if color_name in COLORS and shade:
        return COLORS[color_name].get(shade, COLORS[color_name]["500"])

    return None


def parse_color_class(class_name: str) -> Tuple[str, str, float]:
    """Parse a color class like 'bg-blue-500/50' into components.

    Args:
        class_name: Tailwind class name

    Returns:
        Tuple of (property_prefix, hex_color, opacity)
        opacity is 100 if not specified
    """
    # Check for opacity modifier
    opacity = 100.0
    if "/" in class_name:
        class_name, opacity_str = class_name.rsplit("/", 1)
        try:
            opacity = float(opacity_str)
        except ValueError:
            opacity = 100.0

    # Parse the class
    parts = class_name.split("-")
    if len(parts) < 2:
        return None, None, opacity

    prefix = parts[0]
    color_parts = parts[1:]

    # Handle special colors (bg-white, text-black, etc.)
    if len(color_parts) == 1 and color_parts[0] in SPECIAL_COLORS:
        return prefix, SPECIAL_COLORS[color_parts[0]], opacity

    # Handle regular colors (bg-blue-500, text-slate-400, etc.)
    if len(color_parts) >= 2:
        color_name = color_parts[0]
        shade = color_parts[1]
        if color_name in COLORS and shade in COLORS[color_name]:
            return prefix, COLORS[color_name][shade], opacity

    return None, None, opacity


def _resolve_single_class(class_name: str) -> Dict[str, str]:
    """Convert a single Tailwind class to CSS properties.

    Args:
        class_name: Single Tailwind class name (without variant prefix)

    Returns:
        Dictionary of CSS properties
    """
    result = {}

    # Check static mappings first
    if class_name in FONT_SIZE:
        return FONT_SIZE[class_name].copy()

    if class_name in FONT_WEIGHT:
        return {"font-weight": FONT_WEIGHT[class_name]}

    if class_name in LINE_HEIGHT:
        return {"line-height": LINE_HEIGHT[class_name]}

    if class_name in LETTER_SPACING:
        return {"letter-spacing": LETTER_SPACING[class_name]}

    if class_name in TEXT_ALIGN:
        return {"text-align": TEXT_ALIGN[class_name]}

    if class_name in TEXT_TRANSFORM:
        return {"text-transform": TEXT_TRANSFORM[class_name]}

    if class_name in TEXT_DECORATION:
        return {"text-decoration-line": TEXT_DECORATION[class_name]}

    if class_name in TEXT_OVERFLOW:
        return TEXT_OVERFLOW[class_name].copy()

    if class_name in WHITESPACE:
        return {"white-space": WHITESPACE[class_name]}

    if class_name in WORD_BREAK:
        return WORD_BREAK[class_name].copy()

    if class_name in DISPLAY:
        return {"display": DISPLAY[class_name]}

    if class_name in FLEX_DIRECTION:
        return {"flex-direction": FLEX_DIRECTION[class_name]}

    if class_name in FLEX_WRAP:
        return {"flex-wrap": FLEX_WRAP[class_name]}

    if class_name in FLEX:
        return {"flex": FLEX[class_name]}

    if class_name in FLEX_GROW:
        return {"flex-grow": FLEX_GROW[class_name]}

    if class_name in FLEX_SHRINK:
        return {"flex-shrink": FLEX_SHRINK[class_name]}

    if class_name in JUSTIFY_CONTENT:
        return {"justify-content": JUSTIFY_CONTENT[class_name]}

    if class_name in ALIGN_ITEMS:
        return {"align-items": ALIGN_ITEMS[class_name]}

    if class_name in ALIGN_SELF:
        return {"align-self": ALIGN_SELF[class_name]}

    if class_name in ALIGN_CONTENT:
        return {"align-content": ALIGN_CONTENT[class_name]}

    if class_name in POSITION:
        return {"position": POSITION[class_name]}

    if class_name in Z_INDEX:
        return {"z-index": Z_INDEX[class_name]}

    if class_name in WIDTH_SPECIAL:
        return {"width": WIDTH_SPECIAL[class_name]}

    if class_name in HEIGHT_SPECIAL:
        return {"height": HEIGHT_SPECIAL[class_name]}

    if class_name in WIDTH_FRACTIONS:
        return {"width": WIDTH_FRACTIONS[class_name]}

    if class_name in HEIGHT_FRACTIONS:
        return {"height": HEIGHT_FRACTIONS[class_name]}

    if class_name in MIN_WIDTH:
        return {"min-width": MIN_WIDTH[class_name]}

    if class_name in MAX_WIDTH:
        return {"max-width": MAX_WIDTH[class_name]}

    if class_name in MIN_HEIGHT:
        return {"min-height": MIN_HEIGHT[class_name]}

    if class_name in MAX_HEIGHT:
        return {"max-height": MAX_HEIGHT[class_name]}

    if class_name in SHADOW:
        return {"box-shadow": SHADOW[class_name]}

    if class_name in OPACITY:
        return {"opacity": OPACITY[class_name]}

    if class_name in BLUR:
        return {"filter": BLUR[class_name]}

    if class_name in BG_GRADIENT:
        return {"background-image": BG_GRADIENT[class_name]}

    if class_name in BG_SIZE:
        return {"background-size": BG_SIZE[class_name]}

    if class_name in BG_POSITION:
        return {"background-position": BG_POSITION[class_name]}

    if class_name in BG_REPEAT:
        return {"background-repeat": BG_REPEAT[class_name]}

    if class_name in TRANSITION:
        return TRANSITION[class_name].copy()

    if class_name in DURATION:
        return {"transition-duration": DURATION[class_name]}

    if class_name in TIMING_FUNCTION:
        return {"transition-timing-function": TIMING_FUNCTION[class_name]}

    if class_name in DELAY:
        return {"transition-delay": DELAY[class_name]}

    if class_name in CURSOR:
        return {"cursor": CURSOR[class_name]}

    if class_name in USER_SELECT:
        return {"user-select": USER_SELECT[class_name]}

    if class_name in POINTER_EVENTS:
        return {"pointer-events": POINTER_EVENTS[class_name]}

    if class_name in OBJECT_FIT:
        return {"object-fit": OBJECT_FIT[class_name]}

    if class_name in OBJECT_POSITION:
        return {"object-position": OBJECT_POSITION[class_name]}

    if class_name in VISIBILITY:
        return {"visibility": VISIBILITY[class_name]}

    if class_name in BOX_SIZING:
        return {"box-sizing": BOX_SIZING[class_name]}

    if class_name in ASPECT_RATIO:
        return {"aspect-ratio": ASPECT_RATIO[class_name]}

    if class_name in GRID_TEMPLATE_COLUMNS:
        return {"grid-template-columns": GRID_TEMPLATE_COLUMNS[class_name]}

    if class_name in GRID_TEMPLATE_ROWS:
        return {"grid-template-rows": GRID_TEMPLATE_ROWS[class_name]}

    if class_name in GRID_COLUMN:
        return {"grid-column": GRID_COLUMN[class_name]}

    if class_name in GRID_ROW:
        return {"grid-row": GRID_ROW[class_name]}

    if class_name in GRID_AUTO_FLOW:
        return {"grid-auto-flow": GRID_AUTO_FLOW[class_name]}

    if class_name in GRID_AUTO_COLUMNS:
        return {"grid-auto-columns": GRID_AUTO_COLUMNS[class_name]}

    if class_name in GRID_AUTO_ROWS:
        return {"grid-auto-rows": GRID_AUTO_ROWS[class_name]}

    if class_name in PLACE_CONTENT:
        return {"place-content": PLACE_CONTENT[class_name]}

    if class_name in PLACE_ITEMS:
        return {"place-items": PLACE_ITEMS[class_name]}

    if class_name in PLACE_SELF:
        return {"place-self": PLACE_SELF[class_name]}

    if class_name in RING_WIDTH:
        return RING_WIDTH[class_name].copy()

    if class_name in OUTLINE_STYLE:
        return OUTLINE_STYLE[class_name].copy()

    if class_name in OUTLINE_WIDTH:
        return {"outline-width": OUTLINE_WIDTH[class_name]}

    if class_name in OUTLINE_OFFSET:
        return {"outline-offset": OUTLINE_OFFSET[class_name]}

    # Handle overflow (needs special handling for x/y variants)
    if class_name.startswith("overflow-"):
        if class_name.startswith("overflow-x-"):
            val = class_name.replace("overflow-x-", "")
            return {"overflow-x": OVERFLOW.get(f"overflow-{val}", val)}
        elif class_name.startswith("overflow-y-"):
            val = class_name.replace("overflow-y-", "")
            return {"overflow-y": OVERFLOW.get(f"overflow-{val}", val)}
        elif class_name in OVERFLOW:
            return {"overflow": OVERFLOW[class_name]}

    # Handle border radius
    if class_name.startswith("rounded"):
        # Check for directional variants
        if class_name in BORDER_RADIUS:
            return {"border-radius": BORDER_RADIUS[class_name]}

        # Parse directional rounded classes like rounded-t-lg, rounded-tl-xl
        match = re.match(r"rounded-([trbl]{1,2})-?(.+)?", class_name)
        if match:
            direction = match.group(1)
            size = match.group(2) or ""
            size_key = f"rounded-{size}" if size else "rounded"
            radius = BORDER_RADIUS.get(size_key, "0.25rem")

            direction_map = {
                "t": ["border-top-left-radius", "border-top-right-radius"],
                "r": ["border-top-right-radius", "border-bottom-right-radius"],
                "b": ["border-bottom-left-radius", "border-bottom-right-radius"],
                "l": ["border-top-left-radius", "border-bottom-left-radius"],
                "tl": ["border-top-left-radius"],
                "tr": ["border-top-right-radius"],
                "bl": ["border-bottom-left-radius"],
                "br": ["border-bottom-right-radius"],
            }
            if direction in direction_map:
                for prop in direction_map[direction]:
                    result[prop] = radius
                return result

    # Handle border width
    if class_name.startswith("border"):
        # Border width
        if class_name in BORDER_WIDTH:
            return {"border-width": BORDER_WIDTH[class_name]}

        # Border style
        if class_name in BORDER_STYLE:
            return {"border-style": BORDER_STYLE[class_name]}

        # Check if this is a border color class first (border-{color}-{shade})
        # Must check this BEFORE directional patterns to avoid matching border-rose as border-r
        prefix, hex_color, opacity = parse_color_class(class_name)
        if hex_color and prefix == "border":
            if opacity < 100:
                color_value = hex_to_rgba(hex_color, opacity) if hex_color.startswith("#") else hex_color
            else:
                color_value = hex_color
            return {"border-color": color_value}

        # Directional border widths - only match if followed by optional digit or end of string
        # Pattern: border-t, border-r, border-b, border-l, border-x, border-y
        # With optional width: border-t-2, border-r-4, etc.
        match = re.match(r"^border-([trblxy])(?:-(\d+))?$", class_name)
        if match:
            direction = match.group(1)
            width = match.group(2)
            width_val = f"{width}px" if width else "1px"

            direction_map = {
                "t": ["border-top-width"],
                "r": ["border-right-width"],
                "b": ["border-bottom-width"],
                "l": ["border-left-width"],
                "x": ["border-left-width", "border-right-width"],
                "y": ["border-top-width", "border-bottom-width"],
            }
            if direction in direction_map:
                for prop in direction_map[direction]:
                    result[prop] = width_val
                return result

    # Handle spacing classes (padding, margin, gap)
    spacing_patterns = [
        (r"^p-(.+)$", "padding"),
        (r"^px-(.+)$", ["padding-left", "padding-right"]),
        (r"^py-(.+)$", ["padding-top", "padding-bottom"]),
        (r"^pt-(.+)$", "padding-top"),
        (r"^pr-(.+)$", "padding-right"),
        (r"^pb-(.+)$", "padding-bottom"),
        (r"^pl-(.+)$", "padding-left"),
        (r"^ps-(.+)$", "padding-inline-start"),
        (r"^pe-(.+)$", "padding-inline-end"),
        (r"^m-(.+)$", "margin"),
        (r"^mx-(.+)$", ["margin-left", "margin-right"]),
        (r"^my-(.+)$", ["margin-top", "margin-bottom"]),
        (r"^mt-(.+)$", "margin-top"),
        (r"^mr-(.+)$", "margin-right"),
        (r"^mb-(.+)$", "margin-bottom"),
        (r"^ml-(.+)$", "margin-left"),
        (r"^ms-(.+)$", "margin-inline-start"),
        (r"^me-(.+)$", "margin-inline-end"),
        (r"^gap-(.+)$", "gap"),
        (r"^gap-x-(.+)$", "column-gap"),
        (r"^gap-y-(.+)$", "row-gap"),
        (r"^w-(.+)$", "width"),
        (r"^h-(.+)$", "height"),
        (r"^min-w-(.+)$", "min-width"),
        (r"^max-w-(.+)$", "max-width"),
        (r"^min-h-(.+)$", "min-height"),
        (r"^max-h-(.+)$", "max-height"),
        (r"^inset-(.+)$", ["top", "right", "bottom", "left"]),
        (r"^inset-x-(.+)$", ["left", "right"]),
        (r"^inset-y-(.+)$", ["top", "bottom"]),
        (r"^top-(.+)$", "top"),
        (r"^right-(.+)$", "right"),
        (r"^bottom-(.+)$", "bottom"),
        (r"^left-(.+)$", "left"),
        (r"^start-(.+)$", "inset-inline-start"),
        (r"^end-(.+)$", "inset-inline-end"),
    ]

    for pattern, css_prop in spacing_patterns:
        match = re.match(pattern, class_name)
        if match:
            value_key = match.group(1)

            # Handle negative values
            negative = value_key.startswith("-")
            if negative:
                value_key = value_key[1:]

            # Handle 'auto' value
            if value_key == "auto":
                css_value = "auto"
            elif value_key in SPACING:
                css_value = SPACING[value_key]
                if negative:
                    css_value = f"-{css_value}"
            else:
                continue

            if isinstance(css_prop, list):
                for prop in css_prop:
                    result[prop] = css_value
            else:
                result[css_prop] = css_value
            return result

    # Handle space-x and space-y (child spacing)
    if class_name.startswith("space-x-"):
        value_key = class_name[8:]
        if value_key in SPACING:
            # This creates a CSS variable approach
            return {"--tw-space-x-reverse": "0", "column-gap": SPACING[value_key]}

    if class_name.startswith("space-y-"):
        value_key = class_name[8:]
        if value_key in SPACING:
            return {"--tw-space-y-reverse": "0", "row-gap": SPACING[value_key]}

    # Handle color classes (bg-, text-, border-, ring-, from-, to-, via-)
    prefix, hex_color, opacity = parse_color_class(class_name)
    if hex_color:
        if opacity < 100:
            color_value = hex_to_rgba(hex_color, opacity) if hex_color.startswith("#") else hex_color
        else:
            color_value = hex_color

        color_properties = {
            "bg": "background-color",
            "text": "color",
            "border": "border-color",
            "ring": "--tw-ring-color",
            "outline": "outline-color",
            "accent": "accent-color",
            "caret": "caret-color",
            "fill": "fill",
            "stroke": "stroke",
            "from": "--tw-gradient-from",
            "to": "--tw-gradient-to",
            "via": "--tw-gradient-via",
        }

        if prefix in color_properties:
            return {color_properties[prefix]: color_value}

    return result


def tw(*classes: str) -> Dict[str, str]:
    """Convert Tailwind classes to a CSS dictionary (base styles only).

    Args:
        *classes: Tailwind CSS class names

    Returns:
        Dictionary mapping CSS property names to values

    Example:
        >>> tw("bg-slate-800", "rounded-lg", "p-4")
        {'background-color': '#1e293b', 'border-radius': '0.5rem', 'padding': '1rem'}
    """
    result = {}
    for class_name in classes:
        # Skip variant prefixes for the simple tw() function
        if ":" in class_name:
            base_class = class_name.split(":")[-1]
        else:
            base_class = class_name

        css = _resolve_single_class(base_class)
        result.update(css)

    return result


def parse_tailwind_classes(classes: Union[Tuple[str, ...], list]) -> Dict[str, Dict[str, str]]:
    """Parse Tailwind classes into categorized CSS dictionaries.

    Supports variant prefixes: hover:, focus:, active:

    Args:
        classes: Tuple or list of Tailwind class names

    Returns:
        Dictionary with keys 'base', 'hover', 'focus', 'active',
        each containing a CSS properties dictionary

    Example:
        >>> parse_tailwind_classes(("bg-slate-800", "hover:bg-slate-700", "p-4"))
        {
            'base': {'background-color': '#1e293b', 'padding': '1rem'},
            'hover': {'background-color': '#334155'},
            'focus': {},
            'active': {}
        }
    """
    result = {
        "base": {},
        "hover": {},
        "focus": {},
        "active": {},
    }

    for class_name in classes:
        # Parse variant prefix
        variant = "base"
        base_class = class_name

        if class_name.startswith("hover:"):
            variant = "hover"
            base_class = class_name[6:]
        elif class_name.startswith("focus:"):
            variant = "focus"
            base_class = class_name[6:]
        elif class_name.startswith("active:"):
            variant = "active"
            base_class = class_name[7:]

        # Resolve the class
        css = _resolve_single_class(base_class)
        result[variant].update(css)

    return result


def tailwind_to_css(classes: str) -> Dict[str, str]:
    """Convert a space-separated string of Tailwind classes to CSS.

    Args:
        classes: Space-separated Tailwind class names

    Returns:
        Dictionary mapping CSS property names to values

    Example:
        >>> tailwind_to_css("bg-blue-500 text-white p-4 rounded-lg")
        {'background-color': '#3b82f6', 'color': '#ffffff', 'padding': '1rem', 'border-radius': '0.5rem'}
    """
    class_list = classes.split()
    return tw(*class_list)
