import { FMGlobalChat } from '@/components/fm-global-chat';

export default function FMGlobalPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            FM Global 8-34 ASRS Expert System
          </h1>
          <p className="text-gray-600">
            Automated Storage & Retrieval Systems Fire Protection Guidance
          </p>
        </div>
        
        <FMGlobalChat />
        
        <div className="mt-8 max-w-4xl mx-auto">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">About This System</h3>
            <p className="text-blue-800 text-sm">
              This AI-powered expert system provides guidance on FM Global 8-34 requirements for
              Automated Storage and Retrieval Systems (ASRS). It can help with fire protection design,
              cost optimization, seismic requirements, and specific table/figure references.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}