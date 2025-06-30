import { Brain, ChevronDown } from 'lucide-react';
import { LLMModel } from '../types';

const models: LLMModel[] = [
  { 
    id: 'gpt-4',
    name: 'GPT-4',
    description: 'Most advanced OpenAI model with deep financial understanding'
  },
  {
    id: 'gpt-4-turbo',
    name: 'GPT-4 Turbo',
    description: 'Faster version of GPT-4 with recent knowledge cutoff'
  },
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    description: 'Balanced performance and cost effectiveness'
  },
  {
    id: 'gpt-mini',
    name: 'ChatGPT Mini',
    description: 'Lightweight model for basic financial analysis'
  },
  {
    id: 'claude-3-opus',
    name: 'Claude 3 Opus',
    description: 'Most capable Anthropic model for complex financial analysis'
  },
  {
    id: 'claude-3-sonnet',
    name: 'Claude 3 Sonnet',
    description: 'Balanced Claude model for efficient analysis'
  },
  {
    id: 'claude-3-haiku',
    name: 'Claude 3 Haiku',
    description: 'Fast, efficient Claude model for basic analysis'
  },
  {
    id: 'mistral-large',
    name: 'Mistral Large',
    description: 'Open-source model optimized for financial tasks'
  },
  {
    id: 'ollama-3.2',
    name: 'Ollama 3.2',
    description: 'Open-source LLM with strong financial analysis capabilities'
  }
];

interface ModelSelectorProps {
  selectedModel: string;
  onModelSelect: (modelId: string) => void;
}

export default function ModelSelector({ selectedModel, onModelSelect }: ModelSelectorProps) {
  const selectedModelData = models.find(model => model.id === selectedModel);

  return (
    <div className="bg-white rounded-lg p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="h-5 w-5 text-blue-600" />
        <h2 className="text-lg font-semibold text-gray-900">Select LLM Model</h2>
      </div>
      
      <div className="relative">
        <select
          value={selectedModel}
          onChange={(e) => onModelSelect(e.target.value)}
          className="w-full p-3 bg-white border border-gray-300 rounded-lg appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {models.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
      </div>
      
      {selectedModelData && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900">{selectedModelData.name}</h3>
          <p className="text-sm text-gray-600 mt-1">{selectedModelData.description}</p>
        </div>
      )}
    </div>
  );
}