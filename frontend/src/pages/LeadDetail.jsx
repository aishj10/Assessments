import React, { useEffect, useState } from "react";
import OutboundComposer from "../components/OutboundComposer";
import LeadForm from "../components/LeadForm";
import ScoringWeights from "../components/ScoringWeights";

export default function LeadDetail({leadId, onBack}) {
  const [lead, setLead] = useState(null);
  const [outreach, setOutreach] = useState(null);
  const [loading, setLoading] = useState(true);
  const [qualifying, setQualifying] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [editing, setEditing] = useState(false);
  const [showScoringWeights, setShowScoringWeights] = useState(false);
  const [scoringWeights, setScoringWeights] = useState({
    company_size: 1,
    industry_fit: 2,
    funding: 1,
    decision_maker: 2,
    tech_stack: 1,
    revenue: 1
  });
  
  useEffect(()=>{
    fetch(`/api/leads/${leadId}`)
      .then(r=>r.json())
      .then(data => {
        setLead(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching lead:", err);
        setLoading(false);
      });
  }, [leadId]);

  function qualify() {
    setQualifying(true);
    fetch("/api/leads/qualify", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({lead_id: leadId, scoring_weights: scoringWeights})
    })
    .then(r=>r.json())
    .then(res=>{
      if (res.detail) {
        // API returned an error
        throw new Error(res.detail);
      }
      
      setLead(prev=>({...prev, score: res.score, stage: res.stage}));
      
      // Safely access grok_output with fallbacks
      const justification = res.grok_output?.justification || "No justification provided";
      const breakdown = res.grok_output?.breakdown ? JSON.stringify(res.grok_output.breakdown, null, 2) : "No breakdown available";
      
      alert(`Qualification complete! Score: ${res.score}/100\nStage: ${res.stage}\n\nJustification: ${justification}\n\nBreakdown:\n${breakdown}`);
    })
    .catch(e=>{
      console.error("Qualification error:", e);
      alert("Error during qualification: " + e.message);
    })
    .finally(() => setQualifying(false));
  }

  function genOutreach() {
    setGenerating(true);
    fetch(`/api/leads/outreach/${leadId}`, {method:"POST"})
    .then(r=>r.json())
    .then(data=>{
      if (data.detail) {
        // API returned an error
        throw new Error(data.detail);
      }
      setOutreach(data.outreach);
    })
    .catch(e=>{
      console.error("Outreach generation error:", e);
      alert("Error generating outreach: " + e.message);
    })
    .finally(() => setGenerating(false));
  }

  const handleUpdateLead = async (leadData) => {
    try {
      const response = await fetch(`/api/leads/${leadId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(leadData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update lead");
      }
      
      const updatedLead = await response.json();
      setLead(updatedLead);
      setEditing(false);
    } catch (error) {
      console.error("Error updating lead:", error);
      throw error;
    }
  };

  if(loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading lead details...</div>
      </div>
    );
  }

  if(!lead) {
    return (
      <div className="text-center py-12">
        <div className="text-red-500 text-lg">Lead not found</div>
        <button className="mt-4 text-blue-600 hover:underline" onClick={onBack}>← Back to Dashboard</button>
      </div>
    );
  }

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

  const parseCompanyMetadata = (metadataStr) => {
    if (!metadataStr) return null;
    try {
      return JSON.parse(metadataStr);
    } catch (e) {
      return null;
    }
  };

  const formatMetadataValue = (value) => {
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    if (typeof value === "object") {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <button 
        className="text-blue-600 hover:underline mb-4 flex items-center"
        onClick={onBack}
      >
        ← Back to Dashboard
      </button>
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{lead.company}</h2>
            {lead.name && <div className="text-lg text-gray-700">{lead.name}</div>}
            {lead.title && <div className="text-gray-600">{lead.title}</div>}
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStageColor(lead.stage)}`}>
              {lead.stage}
            </span>
            <button
              onClick={() => setEditing(true)}
              className="px-3 py-1 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors text-sm font-medium"
              title="Edit lead"
            >
              ✏️ Edit
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <div className="text-sm text-gray-500">Email</div>
            <div className="text-gray-900">{lead.email || "Not provided"}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Phone</div>
            <div className="text-gray-900">{lead.phone || "Not provided"}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Website</div>
            <div className="text-gray-900">
              {lead.website ? (
                <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  {lead.website}
                </a>
              ) : (
                "Not provided"
              )}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Score</div>
            <div className="text-2xl font-bold text-gray-900">{Math.round(lead.score || 0)}/100</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Created</div>
            <div className="text-gray-900">{new Date(lead.created_at).toLocaleDateString()}</div>
          </div>
        </div>

        {/* Company Metadata Section */}
        {lead.company_metadata && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Information</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(() => {
                  try {
                    const metadata = typeof lead.company_metadata === 'string' 
                      ? JSON.parse(lead.company_metadata) 
                      : lead.company_metadata;
                    
                    return Object.entries(metadata).map(([key, value]) => (
                      <div key={key} className="bg-white p-3 rounded-md border">
                        <div className="text-sm text-gray-500 capitalize">
                          {key.replace(/_/g, ' ')}
                        </div>
                        <div className="text-gray-900 font-medium">
                          {value === null || value === undefined ? (
                            <span className="text-gray-400">Not specified</span>
                          ) : Array.isArray(value) ? (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {value.map((item, index) => (
                                <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                                  {item}
                                </span>
                              ))}
                            </div>
                          ) : (
                            value
                          )}
                        </div>
                      </div>
                    ));
                  } catch (error) {
                    return (
                      <div className="col-span-full text-center text-gray-500">
                        Unable to parse company metadata
                      </div>
                    );
                  }
                })()}
              </div>
            </div>
          </div>
        )}
        
                <div className="flex gap-3">
                  <button 
                    onClick={qualify} 
                    disabled={qualifying}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-400 transition-colors font-medium"
                  >
                    {qualifying ? "Qualifying..." : "Run AI Qualification"}
                  </button>
                  <button 
                    onClick={() => setShowScoringWeights(true)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors font-medium"
                    title="Customize scoring criteria weights"
                  >
                    ⚙️ Scoring Weights
                  </button>
                  <button 
                    onClick={genOutreach} 
                    disabled={generating}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-green-400 transition-colors font-medium"
                  >
                    {generating ? "Generating..." : "Generate Outreach"}
                  </button>
                </div>
      </div>

      {outreach && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Generated Outreach</h3>
          <div className="space-y-4">
            <div>
              <div className="text-sm text-gray-500 mb-1">Subject Line</div>
              <div className="text-gray-900 font-medium">{outreach.subject}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500 mb-2">Email Body</div>
              <div className="bg-gray-50 p-4 rounded-md">
                <pre className="whitespace-pre-wrap text-gray-900 font-mono text-sm">{outreach.body}</pre>
              </div>
            </div>
            {outreach.tags && outreach.tags.length > 0 && (
              <div>
                <div className="text-sm text-gray-500 mb-2">Tags</div>
                <div className="flex flex-wrap gap-2">
                  {outreach.tags.map((tag, index) => (
                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <OutboundComposer lead={lead} />

      {/* Edit Lead Form Modal */}
      {editing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <LeadForm
              lead={lead}
              onSave={handleUpdateLead}
              onCancel={() => setEditing(false)}
              isEditing={true}
            />
          </div>
        </div>
      )}

      {/* Scoring Weights Modal */}
      {showScoringWeights && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <ScoringWeights
              weights={scoringWeights}
              onWeightsChange={setScoringWeights}
              onClose={() => setShowScoringWeights(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
