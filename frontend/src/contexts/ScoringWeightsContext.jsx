import React, { createContext, useContext, useState, useEffect } from 'react';

const ScoringWeightsContext = createContext();

// Default global scoring weights
const DEFAULT_WEIGHTS = {
  company_size: 3,
  industry_fit: 5,
  funding: 2,
  decision_maker: 4,
  tech_stack: 2,
  revenue: 3
};

export const ScoringWeightsProvider = ({ children }) => {
  const [scoringWeights, setScoringWeights] = useState(DEFAULT_WEIGHTS);

  // Load weights from localStorage on mount
  useEffect(() => {
    const savedWeights = localStorage.getItem('scoringWeights');
    if (savedWeights) {
      try {
        const parsedWeights = JSON.parse(savedWeights);
        setScoringWeights(parsedWeights);
      } catch (error) {
        console.error('Error parsing saved scoring weights:', error);
        setScoringWeights(DEFAULT_WEIGHTS);
      }
    }
  }, []);

  // Save weights to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('scoringWeights', JSON.stringify(scoringWeights));
  }, [scoringWeights]);

  const updateScoringWeights = (newWeights) => {
    setScoringWeights(newWeights);
  };

  const resetScoringWeights = () => {
    setScoringWeights(DEFAULT_WEIGHTS);
  };

  const value = {
    scoringWeights,
    updateScoringWeights,
    resetScoringWeights,
    defaultWeights: DEFAULT_WEIGHTS
  };

  return (
    <ScoringWeightsContext.Provider value={value}>
      {children}
    </ScoringWeightsContext.Provider>
  );
};

export const useScoringWeights = () => {
  const context = useContext(ScoringWeightsContext);
  if (!context) {
    throw new Error('useScoringWeights must be used within a ScoringWeightsProvider');
  }
  return context;
};
