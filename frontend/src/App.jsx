import React from "react";
import Dashboard from "./pages/Dashboard";
import LeadDetail from "./pages/LeadDetail";
import { useState } from "react";
import { ScoringWeightsProvider } from "./contexts/ScoringWeightsContext";

export default function App() {
  const [route, setRoute] = useState({name:"dashboard", leadId:null});
  return (
    <ScoringWeightsProvider>
      <div className="min-h-screen bg-gray-50">
        <div className="p-6 font-sans">
          <header className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Grok SDR Demo</h1>
            <p className="text-gray-600 mt-2">AI-powered sales development representative system</p>
          </header>
          {route.name === "dashboard" && <Dashboard onOpen={(id)=>setRoute({name:"lead",leadId:id})} />}
          {route.name === "lead" && <LeadDetail leadId={route.leadId} onBack={()=>setRoute({name:"dashboard"})} />}
        </div>
      </div>
    </ScoringWeightsProvider>
  );
}
