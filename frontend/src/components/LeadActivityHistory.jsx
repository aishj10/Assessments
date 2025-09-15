import React, { useState, useEffect } from 'react';

export default function LeadActivityHistory({ leadId }) {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedActivities, setExpandedActivities] = useState(new Set());

  useEffect(() => {
    if (leadId) {
      fetchActivities();
    }
  }, [leadId]);

  const fetchActivities = async () => {
    try {
      const response = await fetch(`/api/leads/${leadId}/activities`);
      const data = await response.json();
      setActivities(data);
    } catch (error) {
      console.error('Error fetching activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (action) => {
    const icons = {
      'lead_created': '🆕',
      'qualification_completed': '📊',
      'outreach_generated': '📧',
      'stage_progression': '🔄',
      'lead_updated': '✏️',
      'lead_deleted': '🗑️'
    };
    return icons[action] || '📝';
  };

  const getActivityColor = (action) => {
    const colors = {
      'lead_created': 'bg-green-100 text-green-800',
      'qualification_completed': 'bg-blue-100 text-blue-800',
      'outreach_generated': 'bg-purple-100 text-purple-800',
      'stage_progression': 'bg-yellow-100 text-yellow-800',
      'lead_updated': 'bg-gray-100 text-gray-800',
      'lead_deleted': 'bg-red-100 text-red-800'
    };
    return colors[action] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatAction = (action) => {
    const actionMap = {
      'lead_created': 'Lead Created',
      'qualification_completed': 'AI Qualification',
      'outreach_generated': 'Outreach Generated',
      'stage_progression': 'Stage Progressed',
      'lead_updated': 'Lead Updated',
      'lead_deleted': 'Lead Deleted'
    };
    return actionMap[action] || action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const parseActivityDetail = (activity) => {
    try {
      // Try to parse detail as JSON if it contains structured data
      if (activity.detail && activity.detail.includes('{')) {
        const jsonMatch = activity.detail.match(/\{.*\}/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          return { isJson: true, data: parsed, text: activity.detail };
        }
      }
      return { isJson: false, text: activity.detail };
    } catch (error) {
      return { isJson: false, text: activity.detail };
    }
  };

  const getCleanActivityText = (activity) => {
    // For qualification and outreach activities, show clean text without raw JSON
    if (activity.action === 'qualification_completed' || activity.action === 'outreach_generated') {
      // Extract the clean text part before any JSON
      const textPart = activity.detail.split('{')[0].trim();
      return textPart;
    }
    return activity.detail;
  };

  const toggleActivityExpansion = (activityId) => {
    const newExpanded = new Set(expandedActivities);
    if (newExpanded.has(activityId)) {
      newExpanded.delete(activityId);
    } else {
      newExpanded.add(activityId);
    }
    setExpandedActivities(newExpanded);
  };

  const isActivityExpanded = (activityId) => {
    return expandedActivities.has(activityId);
  };

  const renderQualificationDetails = (parsedData) => {
    if (!parsedData.data) return null;
    
    const { score, justification, breakdown } = parsedData.data;
    
    return (
      <div className="mt-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center space-x-2 mb-3">
          <span className="text-2xl font-bold text-blue-900">{score}/100</span>
          <span className="text-sm text-blue-700 font-medium">Qualification Score</span>
        </div>
        
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-blue-800 mb-2">AI Analysis</h4>
          <div className="text-sm text-blue-800 bg-white p-3 rounded border">
            {justification}
          </div>
        </div>
        
        {breakdown && Object.keys(breakdown).length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-blue-800 mb-2">Detailed Breakdown</h4>
            <div className="space-y-2">
              {Object.entries(breakdown).map(([criterion, data]) => (
                <div key={criterion} className="bg-white p-3 rounded border">
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-medium text-blue-800 capitalize">
                      {criterion.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm font-bold text-blue-900">
                      {data.score}/10
                    </span>
                  </div>
                  <div className="text-xs text-blue-600 mb-1">
                    Weighted Score: {data.weighted_score?.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-600">
                    {data.reason}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderOutreachDetails = (parsedData) => {
    if (!parsedData.data) return null;
    
    const { subject, body, tags } = parsedData.data;
    
    return (
      <div className="mt-3 p-4 bg-purple-50 rounded-lg border border-purple-200">
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-purple-800 mb-2">Email Subject</h4>
          <div className="text-sm text-purple-800 bg-white p-3 rounded border font-medium">
            {subject}
          </div>
        </div>
        
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-purple-800 mb-2">Message Content</h4>
          <div className="bg-white p-3 rounded border">
            <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
              {body}
            </div>
          </div>
        </div>
        
        {tags && tags.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-purple-800 mb-2">Tags</h4>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag, index) => (
                <span key={index} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="text-gray-600">Loading activity history...</div>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-500">No activities recorded yet</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Activity History</h3>
      <div className="space-y-3">
        {activities.map((activity, index) => {
          const parsedDetail = parseActivityDetail(activity);
          const hasDetails = (activity.action === 'qualification_completed' || activity.action === 'outreach_generated') && parsedDetail.isJson;
          const isExpanded = isActivityExpanded(activity.id);
          
          return (
            <div key={activity.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <div className="flex items-start space-x-4 p-4">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-lg">
                    {getActivityIcon(activity.action)}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getActivityColor(activity.action)}`}>
                      {formatAction(activity.action)}
                    </span>
                    <span className="text-sm text-gray-500">by {activity.actor}</span>
                  </div>
                  <div className="text-sm text-gray-900 mb-1">{getCleanActivityText(activity)}</div>
                  
                  <div className="flex items-center justify-between mt-2">
                    <div className="text-xs text-gray-500">{formatDate(activity.created_at)}</div>
                    {hasDetails && (
                      <button
                        onClick={() => toggleActivityExpansion(activity.id)}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-1"
                      >
                        <span>{isExpanded ? 'Hide Details' : 'Show Details'}</span>
                        <span className="transform transition-transform duration-200" style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                          ▼
                        </span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Render detailed information for specific activity types */}
              {hasDetails && isExpanded && (
                <div className="border-t border-gray-100">
                  {activity.action === 'qualification_completed' && renderQualificationDetails(parsedDetail)}
                  {activity.action === 'outreach_generated' && renderOutreachDetails(parsedDetail)}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
