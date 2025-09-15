import React, { useState } from "react";

export default function ScoringWeights({ weights, onWeightsChange, onClose }) {
  const [localWeights, setLocalWeights] = useState(weights || {
    company_size: 3,
    industry_fit: 5,
    funding: 2,
    decision_maker: 4,
    tech_stack: 2,
    revenue: 3
  });

  const criteria = [
    {
      key: "company_size",
      label: "Company Size",
      description: "Employee count and company scale",
      maxWeight: 10
    },
    {
      key: "industry_fit",
      label: "Industry Fit",
      description: "Alignment with target industries",
      maxWeight: 10
    },
    {
      key: "funding",
      label: "Recent Funding",
      description: "Recent funding rounds and financial backing",
      maxWeight: 10
    },
    {
      key: "decision_maker",
      label: "Decision Maker",
      description: "Title and decision-making authority",
      maxWeight: 10
    },
    {
      key: "tech_stack",
      label: "Tech Stack",
      description: "Technology alignment and innovation readiness",
      maxWeight: 10
    },
    {
      key: "revenue",
      label: "Revenue",
      description: "Annual revenue and budget availability",
      maxWeight: 10
    }
  ];

  const handleWeightChange = (key, value) => {
    const newWeights = { ...localWeights, [key]: parseInt(value) || 1 };
    setLocalWeights(newWeights);
  };

  const handleSave = () => {
    onWeightsChange(localWeights);
    onClose();
  };

  const handleReset = () => {
    const defaultWeights = {
      company_size: 3,
      industry_fit: 5,
      funding: 2,
      decision_maker: 4,
      tech_stack: 2,
      revenue: 3
    };
    setLocalWeights(defaultWeights);
  };

  const getTotalWeight = () => {
    return Object.values(localWeights).reduce((sum, weight) => sum + weight, 0);
  };

  const getWeightColor = (weight) => {
    if (weight <= 3) return "text-green-600";
    if (weight <= 6) return "text-yellow-600";
    if (weight <= 8) return "text-orange-600";
    return "text-red-600";
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Customize Scoring Weights</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-xl"
        >
          ×
        </button>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-2">
          Adjust the importance of different lead criteria. Higher weights mean that criterion will have more influence on the overall score.
        </p>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-500">Total Weight:</span>
          <span className={`font-medium ${getWeightColor(getTotalWeight())}`}>
            {getTotalWeight()}
          </span>
          <span className="text-gray-400">(Recommended: 12-30)</span>
        </div>
      </div>

      <div className="space-y-4 mb-6">
        {criteria.map((criterion) => (
          <div key={criterion.key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex-1">
              <div className="font-medium text-gray-900">{criterion.label}</div>
              <div className="text-sm text-gray-600">{criterion.description}</div>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="1"
                max={criterion.maxWeight}
                value={localWeights[criterion.key]}
                onChange={(e) => handleWeightChange(criterion.key, e.target.value)}
                className="w-20"
              />
              <div className="w-8 text-center">
                <span className={`font-medium ${getWeightColor(localWeights[criterion.key])}`}>
                  {localWeights[criterion.key]}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
        >
          Apply Weights
        </button>
        <button
          onClick={handleReset}
          className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors font-medium"
        >
          Reset to Default
        </button>
        <button
          onClick={onClose}
          className="px-4 py-2 bg-gray-200 text-gray-600 rounded-md hover:bg-gray-300 transition-colors font-medium"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
