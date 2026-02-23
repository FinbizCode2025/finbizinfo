import React, { createContext, useContext, useState } from 'react';

type AnalysisResults = {
  audit?: string;
  director?: string;
  financial?: string;
};

const AnalysisContext = createContext<{
  results: AnalysisResults;
  setResults: React.Dispatch<React.SetStateAction<AnalysisResults>>;
}>({
  results: {},
  setResults: () => {},
});

export const AnalysisProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [results, setResults] = useState<AnalysisResults>({});
  return (
    <AnalysisContext.Provider value={{ results, setResults }}>
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => useContext(AnalysisContext);