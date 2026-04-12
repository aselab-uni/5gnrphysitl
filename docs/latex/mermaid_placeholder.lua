local function escape_latex(str)
  local replacements = {
    ["\\"] = "\\textbackslash{}",
    ["{"] = "\\{",
    ["}"] = "\\}",
    ["$"] = "\\$",
    ["&"] = "\\&",
    ["#"] = "\\#",
    ["^"] = "\\^{}",
    ["_"] = "\\_",
    ["~"] = "\\~{}",
    ["%"] = "\\%%",
  }
  return (str:gsub("[\\{}$&#%^_~%%]", replacements))
end

function CodeBlock(el)
  for _, class_name in ipairs(el.classes) do
    if class_name == "mermaid" then
      local first_line = el.text:match("([^\n]+)") or ""
      local latex = table.concat({
        "\\begin{figure}[H]",
        "\\centering",
        "\\fbox{\\begin{minipage}{0.92\\linewidth}",
        "\\small",
        "\\textbf{Mermaid diagram placeholder}\\\\",
        "Ban goc Markdown/Wiki co so do Mermaid se render tren GitHub.\\\\",
        "Ban LaTeX/PDF nay giu cho cho hinh de ban co the thay bang hinh render sau.\\\\[0.5em]",
        "\\textit{Dong dau tien cua so do:} " .. escape_latex(first_line),
        "\\end{minipage}}",
        "\\caption{Placeholder cho so do Mermaid. Neu can ban in an/chuyen nghiep hon, hay render Mermaid thanh SVG/PNG roi thay vao day.}",
        "\\end{figure}",
      }, "\n")
      return pandoc.RawBlock("latex", latex)
    end
  end
  return nil
end
