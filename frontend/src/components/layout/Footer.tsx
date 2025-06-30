import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">About Us</h3>
            <p className="text-sm">
              We combine advanced AI with financial expertise to deliver 
              actionable insights from your financial statements.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Features</h3>
            <ul className="space-y-2 text-sm">
              <li>Financial Ratio Analysis</li>
              <li>Compliance Checking</li>
              <li>Custom Analysis Queries</li>
              <li>AI-Powered Insights</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li>Documentation</li>
              <li>API Reference</li>
              <li>Case Studies</li>
              <li>Blog</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Contact</h3>
            <ul className="space-y-2 text-sm">
              <li>support@luthradigital.com</li>
              <li>+91 11 40195919</li>
              <li>Follow us on LinkedIn</li>
              <li>Follow us on Twitter</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-center">
          © {new Date().getFullYear()} Financial Analysis Suite. All rights reserved.
        </div>
      </div>
    </footer>
  );
}