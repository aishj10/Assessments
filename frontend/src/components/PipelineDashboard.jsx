import React, { useState, useEffect } from 'react';

export default function PipelineDashboard() {
  const [pipelineStats, setPipelineStats] = useState({});
  const [pipelineAnalytics, setPipelineAnalytics] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPipelineData();
  }, []);

  const fetchPipelineData = async () => {
    try {
      const [statsResponse, analyticsResponse] = await Promise.all([
        fetch('/api/leads/pipeline/stats'),
        fetch('/api/leads/pipeline/analytics')
      ]);
      
      const stats = await statsResponse.json();
      const analytics = await analyticsResponse.json();
      
      setPipelineStats(stats);
      setPipelineAnalytics(analytics);
    } catch (error) {
      console.error('Error fetching pipeline data:', error);
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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading pipeline data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Pipeline Statistics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Overview</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Object.entries(pipelineStats).map(([stage, count]) => (
            <div key={stage} className="text-center">
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStageColor(stage)}`}>
                {stage}
              </div>
              <div className="text-2xl font-bold text-gray-900 mt-2">{count}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Conversion Metrics */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversion Metrics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Leads</span>
              <span className="text-xl font-bold text-gray-900">{pipelineAnalytics.total_leads}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Conversion Rate</span>
              <span className="text-xl font-bold text-green-600">{pipelineAnalytics.conversion_rate}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Won</span>
              <span className="text-lg font-semibold text-green-600">{pipelineAnalytics.won_count}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Lost</span>
              <span className="text-lg font-semibold text-red-600">{pipelineAnalytics.lost_count}</span>
            </div>
          </div>
        </div>

        {/* Recent Activities */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {pipelineAnalytics.recent_activities?.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900">
                    {activity.action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div className="text-sm text-gray-600">{activity.detail}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {formatDate(activity.created_at)} • Lead #{activity.lead_id}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
