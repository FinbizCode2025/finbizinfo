import React from 'react';

interface FormatterProps {
  text: string;
}

// Helper function to parse a line for double-asterisk (**bold**) Markdown
const formatTextWithInlineBold = (text: string) => {
  // Regex to find content enclosed in **...**
  // It captures the parts of the string: text before, the **content**, and text after.
  // We use a non-greedy match [^*]*? to stop at the first **
  const regex = /(\s*\*\*([^*]+)\*\*\s*)/g;
  const parts = text.split(regex).filter(part => part !== '');

  const elements: React.ReactNode[] = [];
  let currentText = text;

  // Iterate over the string, finding matches and splitting the string accordingly
  while(currentText.length > 0) {
      const match = currentText.match(regex);

      if (match) {
          const matchedString = match[0];
          const matchIndex = currentText.indexOf(matchedString);

          // 1. Add the plain text before the match
          if (matchIndex > 0) {
              elements.push(<span key={elements.length}>{currentText.substring(0, matchIndex)}</span>);
          }

          // 2. Extract the content inside the asterisks (using a second, simpler regex)
          const boldContentMatch = matchedString.match(/\*\*([^*]+)\*\*/);
          if (boldContentMatch && boldContentMatch[1]) {
              elements.push(
                  <strong key={elements.length}>
                      {/* Trim the surrounding whitespace from the content before rendering */}
                      {boldContentMatch[1].trim()}
                  </strong>
              );
          } else {
              // If regex failed (e.g., malformed markdown), render the matched string as is
              elements.push(<span key={elements.length}>{matchedString}</span>);
          }

          // 3. Move the pointer past the processed match
          currentText = currentText.substring(matchIndex + matchedString.length);
      } else {
          // No more matches, add the rest of the text and exit
          elements.push(<span key={elements.length}>{currentText}</span>);
          currentText = "";
      }
  }

  return elements;
};


const ReportFormatter: React.FC<FormatterProps> = ({ text }) => {
  if (!text) {
    return null;
  }

  // Split the text into lines/paragraphs.
  const lines = text.split('\n');

  return (
    <div className="report-content">
      {lines.map((line, index) => {
        const trimmedLine = line.trim();

        // 💡 1. Structural Formatting Checks

        // Pattern for Final Answers/Conclusions: Highlight yellow. (Kept the original logic)
        const isFinalAnswer = 
          trimmedLine.toLowerCase().startsWith('final answer:') ||
          trimmedLine.toLowerCase().startsWith('conclusion:') ||
          trimmedLine.toLowerCase().startsWith('summary:') ||
          trimmedLine.toLowerCase().startsWith('overall assessment:');
        
        // We REMOVE the old 'isHeading' check and rely only on inline formatting (Step 2).
        
        
        // --- Apply Formatting ---

        // 💡 2. Apply inline bold formatting to the entire line content.
        const formattedContent = formatTextWithInlineBold(line);
        
        if (isFinalAnswer) {
          // Apply line-level styles for final answer (Highlight Yellow)
          return (
            <p 
              key={index} 
              style={{ 
                backgroundColor: 'yellow', 
                fontWeight: 'bold', 
                padding: '4px 6px', 
                borderRadius: '4px',
                margin: '5px 0'
              }}
            >
              {formattedContent}
            </p>
          );
        }

        // Apply line-level styles for text that contains bolded parts.
        // NOTE: We no longer have the old 'isHeading' structural check, 
        // so we simply render the line with the inline bolding applied.
        return (
          <p key={index} style={{ margin: '0 0 5px 0' }}>
            {formattedContent}
          </p>
        );
      })}
    </div>
  );
};

export default ReportFormatter;