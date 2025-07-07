export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white-300 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">About Us</h3>
            <p className="text-sm foot">
              We combine advanced AI with financial expertise to deliver 
              actionable insights from your financial statements.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Features</h3>
            <ul className="space-y-2 text-sm">
              <li className="text-sm foot">Financial Ratio Analysis</li>
              <li className="text-sm foot">Compliance Checking</li>
              <li className="text-sm foot">Custom Analysis Queries</li>
              <li className="text-sm foot">AI-Powered Insights</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li className="text-sm foot">Documentation</li>
              <li className="text-sm foot">API Reference</li>
              <li className="text-sm foot">Case Studies</li>
              <li className="text-sm foot">Blog</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Contact</h3>
            <ul className="space-y-2 text-sm">
              <li className="text-sm foot">support@luthradigital.com</li>
              <li className="text-sm foot">+91 11 40195919</li>
              <li className="text-sm foot">Follow us on LinkedIn</li>
              <li className="text-sm foot">Follow us on Twitter</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-center text-gray-500">
          © {new Date().getFullYear()} Financial Analysis Suite. All rights reserved.
        </div>
      </div>
    </footer>
  );
}