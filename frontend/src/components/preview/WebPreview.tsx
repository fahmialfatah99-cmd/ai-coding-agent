"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  RotateCw,
  ExternalLink,
  Monitor,
  Smartphone,
  Tablet,
  Eye,
  Code2,
  Maximize2,
  Minimize2,
} from "lucide-react";

interface WebPreviewProps {
  code: string;
  filePath?: string;
  onRefresh?: () => void;
}

export const WebPreview: React.FC<WebPreviewProps> = ({
  code,
  filePath = "index.html",
  onRefresh,
}) => {
  const [deviceView, setDeviceView] = useState<"desktop" | "tablet" | "mobile">("desktop");
  const [key, setKey] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Generate complete HTML with proper head/body wrappers and iframe compat
  const generateFullHtml = (rawCode: string): string => {
    if (!rawCode.trim()) {
      return `
        <!DOCTYPE html>
        <html>
          <head>
            <style>
              body {
                background: #0f172a;
                color: #94a3b8;
                font-family: system-ui, -apple-system, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
              }
            </style>
          </head>
          <body>
            <h3>No HTML content to preview</h3>
            <p>Write HTML, CSS, or JS in the editor or ask AI to build a UI.</p>
          </body>
        </html>
      `;
    }

    const iframeCompatScript = `
      <script>
        (function() {
          function forceDismissLoaders() {
            var loader = document.getElementById('loader') || document.querySelector('.preloader') || document.querySelector('#preloader');
            if (loader) {
              loader.style.opacity = '0';
              loader.style.pointerEvents = 'none';
              setTimeout(function() { if (loader) loader.style.display = 'none'; }, 400);
            }
          }
          if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(forceDismissLoaders, 150);
          } else {
            window.addEventListener('DOMContentLoaded', forceDismissLoaders);
            window.addEventListener('load', forceDismissLoaders);
          }
          setTimeout(forceDismissLoaders, 600);
        })();
      </script>
    `;

    let fullHtml = rawCode;
    if (!rawCode.toLowerCase().includes("<html") && !rawCode.toLowerCase().includes("<!doctype")) {
      fullHtml = `
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
              body { font-family: system-ui, -apple-system, sans-serif; }
            </style>
          </head>
          <body class="p-4 bg-slate-900 text-white min-h-screen">
            ${rawCode}
          </body>
        </html>
      `;
    }

    if (fullHtml.includes("</body>")) {
      return fullHtml.replace("</body>", `${iframeCompatScript}</body>`);
    } else if (fullHtml.includes("</html>")) {
      return fullHtml.replace("</html>", `${iframeCompatScript}</html>`);
    }
    return fullHtml + iframeCompatScript;
  };

  const handleRefresh = () => {
    setKey((prev) => prev + 1);
    if (onRefresh) onRefresh();
  };

  const handleOpenNewTab = () => {
    const fullHtml = generateFullHtml(code);
    const blob = new Blob([fullHtml], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  };

  const getContainerWidth = () => {
    switch (deviceView) {
      case "mobile":
        return "max-w-[375px] h-[667px] shadow-2xl rounded-2xl border-4 border-neutral-700";
      case "tablet":
        return "max-w-[768px] h-[900px] shadow-2xl rounded-xl border-4 border-neutral-700";
      case "desktop":
      default:
        return "w-full h-full";
    }
  };

  return (
    <div
      className={`flex flex-col bg-[#141414] border-t border-neutral-800 text-neutral-200 overflow-hidden ${
        isFullscreen ? "fixed inset-0 z-50 bg-[#121212]" : "h-full w-full"
      }`}
    >
      {/* Top Preview Control Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#1a1a1a] border-b border-neutral-800 text-xs select-none">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-[11px] tracking-wide text-neutral-200">
            LIVE WEB PREVIEW
          </span>
          <span className="text-neutral-600">|</span>
          <span className="font-mono text-neutral-400 text-[11px] truncate max-w-[200px]">
            {filePath}
          </span>
        </div>

        {/* Device Mode Switcher */}
        <div className="flex items-center gap-1 bg-neutral-900 p-0.5 rounded border border-neutral-800">
          <button
            onClick={() => setDeviceView("desktop")}
            className={`p-1 rounded transition ${
              deviceView === "desktop"
                ? "bg-accent text-white shadow-sm"
                : "text-neutral-400 hover:text-neutral-200"
            }`}
            title="Desktop View (100%)"
          >
            <Monitor className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setDeviceView("tablet")}
            className={`p-1 rounded transition ${
              deviceView === "tablet"
                ? "bg-accent text-white shadow-sm"
                : "text-neutral-400 hover:text-neutral-200"
            }`}
            title="Tablet View (768px)"
          >
            <Tablet className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setDeviceView("mobile")}
            className={`p-1 rounded transition ${
              deviceView === "mobile"
                ? "bg-accent text-white shadow-sm"
                : "text-neutral-400 hover:text-neutral-200"
            }`}
            title="Mobile View (375px)"
          >
            <Smartphone className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className="p-1.5 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded transition"
            title="Reload Preview"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleOpenNewTab}
            className="p-1.5 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded transition"
            title="Open Preview in New Browser Tab"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded transition"
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Preview"}
          >
            {isFullscreen ? (
              <Minimize2 className="w-3.5 h-3.5" />
            ) : (
              <Maximize2 className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </div>

      {/* Preview Canvas */}
      <div className="flex-1 bg-[#1e1e1e] flex items-center justify-center p-2 overflow-auto">
        <div className={`transition-all duration-300 ${getContainerWidth()} bg-white overflow-hidden`}>
          <iframe
            key={key}
            ref={iframeRef}
            srcDoc={generateFullHtml(code)}
            title="Live Web Preview"
            sandbox="allow-scripts allow-modals allow-forms allow-same-origin"
            className="w-full h-full border-0 bg-white"
          />
        </div>
      </div>
    </div>
  );
};
