import React, { useState } from 'react';

const PIPELINE_STAGES = [
  { value: 'New', label: 'New', description: 'Newly added lead' },
  { value: 'Qualified', label: 'Qualified', description: 'Lead has been qualified' },
  { value: 'Contacted', label: 'Contacted', description: 'Initial outreach made' },
  { value: 'Meeting', label: 'Meeting', description: 'Meeting scheduled/completed' },
  { value: 'Won', label: 'Won', description: 'Deal closed successfully' },
  { value: 'Lost', label: 'Lost', description: 'Deal lost or disqualified' }
];

export default function StageProgression({ leadId, currentStage, onStageUpdated }) {
  const [showModal, setShowModal] = useState(false);
  const [selectedStage, setSelectedStage] = useState(currentStage);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleProgress = async () => {
    if (selectedStage === currentStage) {
      alert('Please select a different stage');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/leads/${leadId}/progress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_stage: selectedStage,
          reason: reason || null
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to progress lead');
      }

      const result = await response.json();
      onStageUpdated(result.stage);
      setShowModal(false);
      setReason('');
      alert('Lead progressed successfully!');
    } catch (error) {
      console.error('Error progressing lead:', error);
      alert('Failed to progress lead: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getStageColor = (stage) => {
    const colors = {
      "New": "bg-gray-100 text-gray-800",
      "Qualified": "bg-blue-100 text-blue-800",
      "Contacted": "bg-yellow-100 text-yellow-800",
      "Meeting": "bg-purple-100 text-purple-800",
      "Won": "bg-green-100 text-green-800",
      "Lost": "bg-red-100 text-red-800"
    };
    return colors[stage] || "bg-gray-100 text-gray-800";
  };

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors font-medium"
        title="Manually progress lead to next stage"
      >
        🔄 Progress Stage
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Progress Lead Stage</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Stage
              </label>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStageColor(currentStage)}`}>
                {currentStage}
              </span>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                New Stage
              </label>
              <select
                value={selectedStage}
                onChange={(e) => setSelectedStage(e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              >
                {PIPELINE_STAGES.map((stage) => (
                  <option key={stage.value} value={stage.value}>
                    {stage.label} - {stage.description}
                  </option>
                ))}
              </select>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reason (Optional)
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Why are you progressing this lead?"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
              <button
                onClick={handleProgress}
                disabled={loading}
                className="px-4 py-2 bg-indigo-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400"
              >
                {loading ? 'Progressing...' : 'Progress Lead'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
