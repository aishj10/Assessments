import React, { useEffect, useState } from "react";
import LeadForm from "../components/LeadForm";
import ScoringWeights from "../components/ScoringWeights";
import PipelineDashboard from "../components/PipelineDashboard";
import SearchSystem from "../components/SearchSystem";
import { useScoringWeights } from "../contexts/ScoringWeightsContext";

export default function Dashboard({onOpen}) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingLead, setEditingLead] = useState(null);
  const [showScoringWeights, setShowScoringWeights] = useState(false);
  const [showSearchSystem, setShowSearchSystem] = useState(false);
  const [activeTab, setActiveTab] = useState('leads');
  const { scoringWeights, updateScoringWeights } = useScoringWeights();
  
  useEffect(()=> {
    fetch("/api/leads")
      .then(r=>r.json())
      .then(data => {
        setLeads(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching leads:", err);
        setLoading(false);
      });
  }, []);

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

  const refreshLeads = () => {
    setLoading(true);
    fetch("/api/leads")
      .then(r => r.json())
      .then(data => {
        setLeads(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching leads:", err);
        setLoading(false);
      });
  };

  const handleCreateLead = async (leadData) => {
    try {
      const response = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(leadData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create lead");
      }
      
      setShowCreateForm(false);
      refreshLeads();
    } catch (error) {
      console.error("Error creating lead:", error);
      throw error;
    }
  };

  const handleUpdateLead = async (leadData) => {
    try {
      const response = await fetch(`/api/leads/${editingLead.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(leadData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update lead");
      }
      
      setEditingLead(null);
      refreshLeads();
    } catch (error) {
      console.error("Error updating lead:", error);
      throw error;
    }
  };

  const handleDeleteLead = async (leadId, leadCompany) => {
    if (!window.confirm(`Are you sure you want to delete the lead for ${leadCompany}? This action cannot be undone.`)) {
      return;
    }
    
    try {
      const response = await fetch(`/api/leads/${leadId}`, {
        method: "DELETE"
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete lead");
      }
      
      refreshLeads();
    } catch (error) {
      console.error("Error deleting lead:", error);
      alert("Failed to delete lead: " + error.message);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Loading leads...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Sales Pipeline</h2>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-600">
            {leads.length} total leads
          </div>
          <button
            onClick={() => setShowSearchSystem(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium"
            title="Search through leads, activities, and company metadata"
          >
            🔍 Search
          </button>
          <button
            onClick={() => setShowScoringWeights(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors font-medium"
            title="Customize global scoring criteria weights (applies to all leads)"
          >
            ⚙️ Global Scoring Weights
          </button>
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
          >
            + Add Lead
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('leads')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'leads'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Leads ({leads.length})
          </button>
          <button
            onClick={() => setActiveTab('pipeline')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'pipeline'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Pipeline Monitoring
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'leads' && (
        <>
          {leads.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-500 text-lg">No leads found</div>
              <div className="text-gray-400 text-sm mt-2">Add some leads to get started</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {leads.map(l => (
            <div key={l.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <div className="text-lg font-semibold text-gray-900">{l.company}</div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStageColor(l.stage)}`}>
                  {l.stage}
                </span>
              </div>
              
              <div className="text-sm text-gray-600 mb-3">
                {l.name && <div>{l.name}</div>}
                {l.title && <div className="text-gray-500">{l.title}</div>}
              </div>

              {/* Company Metadata Preview */}
              {l.company_metadata && (() => {
                try {
                  const metadata = typeof l.company_metadata === 'string' 
                    ? JSON.parse(l.company_metadata) 
                    : l.company_metadata;
                  
                  return (
                    <div className="mb-3">
                      <div className="flex flex-wrap gap-2 text-xs">
                        {metadata.industry && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full">
                            {metadata.industry}
                          </span>
                        )}
                        {metadata.company_size && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                            {metadata.company_size} employees
                          </span>
                        )}
                        {metadata.recent_funding && (
                          <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                            {metadata.recent_funding}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                } catch (error) {
                  return null;
                }
              })()}
              
              <div className="flex justify-between items-center mb-4">
                <div className="text-sm">
                  <span className="text-gray-500">Score: </span>
                  <span className="font-medium text-gray-900">{Math.round(l.score || 0)}/100</span>
                </div>
                <div className="text-xs text-gray-400">
                  {new Date(l.created_at).toLocaleDateString()}
                </div>
              </div>
              
              <div className="flex gap-2">
                <button 
                  className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                  onClick={()=>onOpen(l.id)}
                >
                  View
                </button>
                <button 
                  className="px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors text-sm font-medium"
                  onClick={() => setEditingLead(l)}
                  title="Edit lead"
                >
                  ✏️
                </button>
                <button 
                  className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
                  onClick={() => handleDeleteLead(l.id, l.company)}
                  title="Delete lead"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
        </>
      )}

      {activeTab === 'pipeline' && (
        <PipelineDashboard />
      )}

      {/* Create Lead Form Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <LeadForm
              onSave={handleCreateLead}
              onCancel={() => setShowCreateForm(false)}
              isEditing={false}
            />
          </div>
        </div>
      )}

      {/* Edit Lead Form Modal */}
      {editingLead && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <LeadForm
              lead={editingLead}
              onSave={handleUpdateLead}
              onCancel={() => setEditingLead(null)}
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
                      onWeightsChange={updateScoringWeights}
                      onClose={() => setShowScoringWeights(false)}
                    />
          </div>
        </div>
      )}

      {/* Search System Modal */}
      {showSearchSystem && (
        <SearchSystem
          onLeadSelect={(leadId) => {
            setShowSearchSystem(false);
            onOpen(leadId);
          }}
          onClose={() => setShowSearchSystem(false)}
        />
      )}
    </div>
  );
}
