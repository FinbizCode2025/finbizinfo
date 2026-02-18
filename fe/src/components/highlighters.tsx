import React from 'react';

interface FormatterProps {
  text: string;
}

// This component now handles structural formatting (bolding headers, highlighting conclusions)
const ReportFormatter: React.FC<FormatterProps> = ({ text }) => {
  if (!text) {
    return null;
  }

  // Split the text into lines/paragraphs for easier processing.
  const lines = text.split('\n');

  return (
    <div className="report-content">
      {lines.map((line, index) => {
        const trimmedLine = line.trim();

        // 💡 Pattern for Final Answers/Conclusions: Highlight the entire line yellow.
        const isFinalAnswer = 
          trimmedLine.toLowerCase().startsWith('final answer:') ||
          trimmedLine.toLowerCase().startsWith('conclusion:') ||
          trimmedLine.toLowerCase().startsWith('summary:') ||
          trimmedLine.toLowerCase().startsWith('overall assessment:');
        
        // 💡 Pattern for Headings: Bold the entire line if it ends with a colon or is a short, all-caps phrase.
        const isHeading = 
          trimmedLine.length > 0 && 
          (trimmedLine.endsWith(':') || 
           (trimmedLine.toUpperCase() === trimmedLine && trimmedLine.length < 50 && trimmedLine.length > 5));

        
        // --- Apply Formatting ---
        
        if (isFinalAnswer) {
          // Highlight the entire line yellow
          return (
            <p 
              key={index} 
              style={{ 
                backgroundColor: 'yellow', 
                fontWeight: 'bold', 
                padding: '4px 6px', 
                borderRadius: '4px' 
              }}
            >
              {line}
            </p>
          );
        }

        if (isHeading) {
          // Bold the entire line
          return (
            <p key={index} style={{ fontWeight: 'bold', marginTop: '10px', marginBottom: '5px' }}>
              {line}
            </p>
          );
        }

        // Default rendering (regular text)
        return (
          <p key={index} style={{ margin: '0 0 5px 0' }}>
            {line}
          </p>
        );
      })}
    </div>
  );
};

export default ReportFormatter;