#!/bin/sh
# Render the short report docs/report_{en,zh}.md to outputs/report_{en,zh}.pdf
# (appendix table from outputs/report_appendix.md; pandoc -> HTML -> headless Chrome).
#   python3 scripts/report_tables.py > outputs/report_table.md   # refresh the appendix first
#   sh scripts/report_pdf.sh
set -e
cd "$(dirname "$0")/.."
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
TMP="$(mktemp -d)"
cat > "$TMP/style.css" <<'CSS'
@page { size: A4; margin: 16mm 15mm; }
html, body { background: #fff; }
body { font-family: "Helvetica Neue", Helvetica, Arial, "PingFang SC", "Heiti SC", sans-serif; font-size: 9.6pt; line-height: 1.5; color: #1a1a1a; max-width: none; margin: 0; padding: 0; }
header#title-block-header { border-bottom: 2px solid #1a1a1a; padding-bottom: 8px; margin-bottom: 14px; }
h1.title { font-size: 19pt; margin: 0 0 2px 0; } p.subtitle { font-size: 11pt; color: #555; margin: 0 0 6px 0; }
p.author, p.date { display: inline; font-size: 9.6pt; color: #333; margin: 0; } p.date::before { content: " · "; }
h2 { font-size: 12.5pt; margin: 16px 0 6px 0; color: #111; border-bottom: 1px solid #ddd; padding-bottom: 2px; }
p, li { margin: 4px 0; } ul, ol { padding-left: 18px; margin: 4px 0; }
blockquote { margin: 6px 0; padding: 4px 10px; border-left: 3px solid #888; background: #f6f6f6; }
table { border-collapse: collapse; width: 100%; font-size: 8.4pt; margin: 6px 0 2px 0; }
th, td { border-bottom: 1px solid #d5d5d5; padding: 3px 5px; text-align: left; vertical-align: top; }
th { border-bottom: 1.5px solid #333; background: #fafafa; } tr { page-break-inside: avoid; }
p:has(> em:first-child) { font-size: 8.4pt; color: #444; }
a { color: #1a4fa0; text-decoration: none; }
CSS
for lang in en zh; do
  if [ "$lang" = zh ]; then
    sed -e '1s/.*/| # | 品类 | 品牌数（W\/C） | DeepSeek 第 1 轮 补表前 → 补表后 | 最终 | 留出 | Qwen |/' \
        -e 's/(renamed: /（改名后：/; s/) | Pass/） | Pass/' outputs/report_appendix.md > "$TMP/appendix.md"
  else
    cp outputs/report_appendix.md "$TMP/appendix.md"
  fi
  awk -v f="$TMP/appendix.md" '/<!-- APPENDIX -->/ { while ((getline l < f) > 0) print l; next } { print }' \
    "docs/report_$lang.md" > "$TMP/report_$lang.md"
  pandoc "$TMP/report_$lang.md" -s --embed-resources --css "$TMP/style.css" -o "$TMP/report_$lang.html"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="outputs/report_$lang.pdf" "file://$TMP/report_$lang.html" 2>/dev/null
  echo "outputs/report_$lang.pdf"
done
rm -r "${TMP:?}"
