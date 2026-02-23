import { Star } from 'lucide-react';

const testimonials = [
  {
    name: "Ajay Kaushik",
    role: "Cyprus, Equitium",
    content: "This tool has revolutionized how we analyze our financial statements. The AI-powered insights have helped us identify growth opportunities we might have missed.",
    rating: 5
  },
  {
    name: "Rajesh Sinha",
    role: "Maestro Engineering",
    content: "The automated ratio analysis and compliance checks save us hours of work. It's like having a team of expert analysts at your fingertips.",
    rating: 5
  },
  {
    name: "Priya Patel",
    role: "Investment Manager, Capital Partners",
    content: "The custom analysis feature is brilliant. It helps us quickly answer specific questions about financial performance that would typically require extensive research.",
    rating: 5
  }
];

export default function Testimonials() {
  return (
    <div className="mt-16">
      <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
        What Our Users Say
      </h2>
      <div className="grid md:grid-cols-3 gap-8">
        {testimonials.map((testimonial, index) => (
          <div key={index} className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex gap-1 mb-4">
              {[...Array(testimonial.rating)].map((_, i) => (
                <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
              ))}
            </div>
            <p className="text-gray-600 mb-4">{testimonial.content}</p>
            <div>
              <p className="font-semibold text-gray-900">{testimonial.name}</p>
              <p className="text-sm text-gray-500">{testimonial.role}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}