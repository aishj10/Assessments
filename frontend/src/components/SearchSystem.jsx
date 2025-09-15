import React, { useState, useEffect, useRef } from 'react';

export default function SearchSystem({ onLeadSelect, onClose }) {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [suggestions, setSuggestions] = useState({});
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchInputRef = useRef(null);
  const debounceTimeoutRef = useRef(null);

  useEffect(() => {
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    if (query.length >= 2) {
      // Debounce search
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      
      debounceTimeoutRef.current = setTimeout(() => {
        performSearch();
        getSuggestions();
      }, 300);
    } else {
      setSearchResults(null);
      setSuggestions({});
    }
  }, [query, activeTab]);

  const performSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/leads/search/all?q=${encodeURIComponent(query)}&search_type=${activeTab}&limit=20`);
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSuggestions = async () => {
    if (!query.trim()) return;
    
    try {
      const response = await fetch(`/api/leads/search/suggestions?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setSuggestions(data.suggestions || {});
    } catch (error) {
      console.error('Suggestions error:', error);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    setShowSuggestions(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getMatchTypeColor = (matchType) => {
    const colors = {
      'company': 'bg-blue-100 text-blue-800',
      'contact': 'bg-green-100 text-green-800',
      'title': 'bg-purple-100 text-purple-800',
      'email': 'bg-yellow-100 text-yellow-800',
      'metadata': 'bg-orange-100 text-orange-800',
      'action': 'bg-indigo-100 text-indigo-800',
      'detail': 'bg-pink-100 text-pink-800',
      'actor': 'bg-gray-100 text-gray-800'
    };
    return colors[matchType] || 'bg-gray-100 text-gray-800';
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

  const renderSuggestions = () => {
    const allSuggestions = [
      ...(suggestions.companies || []).map(s => ({ text: s, type: 'company' })),
      ...(suggestions.contacts || []).map(s => ({ text: s, type: 'contact' })),
      ...(suggestions.industries || []).map(s => ({ text: s, type: 'industry' })),
      ...(suggestions.tech_stacks || []).map(s => ({ text: s, type: 'tech' }))
    ];

    if (allSuggestions.length === 0) return null;

    return (
      <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-md shadow-lg z-10 max-h-60 overflow-y-auto">
        {allSuggestions.slice(0, 10).map((suggestion, index) => (
          <button
            key={index}
            onClick={() => handleSuggestionClick(suggestion.text)}
            className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center justify-between"
          >
            <span>{suggestion.text}</span>
            <span className={`px-2 py-1 rounded-full text-xs ${getMatchTypeColor(suggestion.type)}`}>
              {suggestion.type}
            </span>
          </button>
        ))}
      </div>
    );
  };

  const renderSearchResults = () => {
    if (!searchResults) return null;

    const { leads, activities, metadata, total_results } = searchResults;

    return (
      <div className="mt-6 space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Search Results ({total_results})
          </h3>
          <div className="text-sm text-gray-500">
            Found {leads.length} leads, {activities.length} activities, {metadata.length} metadata matches
          </div>
        </div>

        {/* Leads Results */}
        {leads.length > 0 && (
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-3">Leads ({leads.length})</h4>
            <div className="space-y-3">
              {leads.map((lead) => (
                <div
                  key={lead.id}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onLeadSelect(lead.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h5 className="font-semibold text-gray-900">{lead.company}</h5>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStageColor(lead.stage)}`}>
                          {lead.stage}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs ${getMatchTypeColor(lead.match_type)}`}>
                          {lead.match_type}
                        </span>
                      </div>
                      {lead.name && <div className="text-sm text-gray-600">{lead.name} - {lead.title}</div>}
                      {lead.email && <div className="text-sm text-gray-500">{lead.email}</div>}
                      <div className="text-xs text-gray-400 mt-1">
                        Score: {Math.round(lead.score || 0)}/100 • Created: {formatDate(lead.created_at)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        Relevance: {Math.round(lead.relevance_score * 10)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Activities Results */}
        {activities.length > 0 && (
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-3">Activities ({activities.length})</h4>
            <div className="space-y-3">
              {activities.map((activity) => (
                <div
                  key={activity.id}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onLeadSelect(activity.lead_id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h5 className="font-semibold text-gray-900">{activity.lead_company}</h5>
                        <span className={`px-2 py-1 rounded-full text-xs ${getMatchTypeColor(activity.match_type)}`}>
                          {activity.match_type}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 mb-1">
                        {activity.action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </div>
                      <div className="text-sm text-gray-500">
                        {typeof activity.detail === 'string' 
                          ? activity.detail.substring(0, 200) + (activity.detail.length > 200 ? '...' : '')
                          : JSON.stringify(activity.detail).substring(0, 200) + '...'
                        }
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {activity.actor} • {formatDate(activity.created_at)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        Relevance: {Math.round(activity.relevance_score * 10)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata Results */}
        {metadata.length > 0 && (
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-3">Metadata ({metadata.length})</h4>
            <div className="space-y-3">
              {metadata.map((item, index) => (
                <div
                  key={index}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onLeadSelect(item.lead_id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h5 className="font-semibold text-gray-900">{item.company}</h5>
                        <span className="px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-800">
                          {item.field}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        <strong>{item.field}:</strong> {Array.isArray(item.value) ? item.value.join(', ') : item.value}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        Relevance: {Math.round(item.relevance_score * 10)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {total_results === 0 && (
          <div className="text-center py-8">
            <div className="text-gray-500">No results found for "{query}"</div>
            <div className="text-gray-400 text-sm mt-2">Try different keywords or search terms</div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Search System</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          </div>

          {/* Search Input */}
          <div className="relative mb-4">
            <input
              ref={searchInputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setShowSuggestions(true)}
              placeholder="Search leads, activities, company metadata..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
            />
            {loading && (
              <div className="absolute right-3 top-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
            )}
            {showSuggestions && renderSuggestions()}
          </div>

          {/* Search Type Tabs */}
          <div className="flex space-x-1 mb-4">
            {[
              { key: 'all', label: 'All' },
              { key: 'company', label: 'Companies' },
              { key: 'contact', label: 'Contacts' },
              { key: 'metadata', label: 'Metadata' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Results */}
          {renderSearchResults()}
        </div>
      </div>
    </div>
  );
}
