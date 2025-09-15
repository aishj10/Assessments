import React, { useState } from "react";

export default function OutboundComposer({lead}) {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);

  function send() {
    setSending(true);
    // For demo: simulate sending
    setTimeout(() => {
      alert(`Demo: Email would be sent to ${lead.email || "no-email"} at ${lead.company}`);
      setSending(false);
    }, 1000);
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Manual Email Composer</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Subject Line
          </label>
          <input 
            type="text"
            placeholder="Enter email subject..."
            value={subject} 
            onChange={e=>setSubject(e.target.value)} 
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Body
          </label>
          <textarea 
            placeholder="Compose your message..."
            value={body} 
            onChange={e=>setBody(e.target.value)} 
            rows={8}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500">
            To: {lead.email || "No email provided"}
          </div>
          <button 
            onClick={send} 
            disabled={sending || !subject.trim() || !body.trim()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 transition-colors font-medium"
          >
            {sending ? "Sending..." : "Send Email (Demo)"}
          </button>
        </div>
      </div>
    </div>
  );
}
