import React, { useState, useEffect } from "react";

export default function LeadForm({ lead, onSave, onCancel, isEditing = false }) {
  const [formData, setFormData] = useState({
    company: "",
    name: "",
    title: "",
    email: "",
    phone: "",
    website: "",
    company_metadata: {
      company_size: "",
      industry: "",
      recent_funding: "",
      tech_stack: [],
      annual_revenue: "",
      founded: ""
    }
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (lead && isEditing) {
      const metadata = lead.company_metadata ? 
        (typeof lead.company_metadata === 'string' ? 
          JSON.parse(lead.company_metadata) : 
          lead.company_metadata) : {};
      
      setFormData({
        company: lead.company || "",
        name: lead.name || "",
        title: lead.title || "",
        email: lead.email || "",
        phone: lead.phone || "",
        website: lead.website || "",
        company_metadata: {
          company_size: metadata.company_size || "",
          industry: metadata.industry || "",
          recent_funding: metadata.recent_funding || "",
          tech_stack: metadata.tech_stack || [],
          annual_revenue: metadata.annual_revenue || "",
          founded: metadata.founded || ""
        }
      });
    }
  }, [lead, isEditing]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const handleMetadataChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      company_metadata: {
        ...prev.company_metadata,
        [field]: value
      }
    }));
  };

  const handleTechStackChange = (value) => {
    const techStack = value.split(',').map(tech => tech.trim()).filter(tech => tech);
    handleMetadataChange('tech_stack', techStack);
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.company.trim()) {
      newErrors.company = "Company name is required";
    }
    
    if (formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }
    
    if (formData.website && !/^https?:\/\/.+/.test(formData.website)) {
      newErrors.website = "Please enter a valid URL (starting with http:// or https://)";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    try {
      // Clean up empty metadata fields
      const cleanedMetadata = Object.fromEntries(
        Object.entries(formData.company_metadata).filter(([_, value]) => 
          value !== "" && value !== null && value !== undefined && 
          !(Array.isArray(value) && value.length === 0)
        )
      );
      
      const payload = {
        ...formData,
        company_metadata: cleanedMetadata
      };
      
      await onSave(payload);
    } catch (error) {
      console.error("Error saving lead:", error);
      setErrors({ submit: "Failed to save lead. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {isEditing ? "Edit Lead" : "Create New Lead"}
      </h3>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-3">Basic Information</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company Name *
              </label>
              <input
                type="text"
                value={formData.company}
                onChange={(e) => handleInputChange("company", e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.company ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="Enter company name"
              />
              {errors.company && <p className="text-red-500 text-sm mt-1">{errors.company}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contact Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter contact name"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => handleInputChange("title", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter job title"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange("email", e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.email ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="Enter email address"
              />
              {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => handleInputChange("phone", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter phone number"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Website
              </label>
              <input
                type="url"
                value={formData.website}
                onChange={(e) => handleInputChange("website", e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.website ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="https://example.com"
              />
              {errors.website && <p className="text-red-500 text-sm mt-1">{errors.website}</p>}
            </div>
          </div>
        </div>

        {/* Company Metadata */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-3">Company Information</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company Size
              </label>
              <input
                type="number"
                value={formData.company_metadata.company_size}
                onChange={(e) => handleMetadataChange("company_size", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Number of employees"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Industry
              </label>
              <input
                type="text"
                value={formData.company_metadata.industry}
                onChange={(e) => handleMetadataChange("industry", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., SaaS, Finance, Technology"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Recent Funding
              </label>
              <select
                value={formData.company_metadata.recent_funding}
                onChange={(e) => handleMetadataChange("recent_funding", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select funding stage</option>
                <option value="pre-seed">Pre-seed</option>
                <option value="seed">Seed</option>
                <option value="Series A">Series A</option>
                <option value="Series B">Series B</option>
                <option value="Series C">Series C</option>
                <option value="IPO">IPO</option>
                <option value="None">No recent funding</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Annual Revenue
              </label>
              <input
                type="text"
                value={formData.company_metadata.annual_revenue}
                onChange={(e) => handleMetadataChange("annual_revenue", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 10M, 500M"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Founded Year
              </label>
              <input
                type="number"
                value={formData.company_metadata.founded}
                onChange={(e) => handleMetadataChange("founded", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 2020"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tech Stack
              </label>
              <input
                type="text"
                value={formData.company_metadata.tech_stack.join(", ")}
                onChange={(e) => handleTechStackChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Python, React, AWS (comma-separated)"
              />
            </div>
          </div>
        </div>

        {errors.submit && (
          <div className="text-red-500 text-sm">{errors.submit}</div>
        )}

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-400 transition-colors font-medium"
          >
            {loading ? "Saving..." : (isEditing ? "Update Lead" : "Create Lead")}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors font-medium"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
