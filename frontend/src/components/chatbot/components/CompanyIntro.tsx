import React from 'react';
import './CompanyIntro.css'; // External CSS file
import robotImage from '../assets/robot-image.jpg';

const CompanyIntro = () => {
  return (
    <div className="main-page">
      <header className="header">
        <div className="container">
          <h1>Legal Mate</h1>
          <p>
            I am an AI agent and I help you resolve issues on FEMA, balance, finance, and various matters pertaining to the legal framework in India and further such things.
          </p>
        </div>
      </header>

      <section className="chatbot-section">
        <div className="container">
          <div className="robot-image-container">
            <img src={robotImage} alt="Legal Bot" className="robot-image" />
          </div>
          <p>
            I am here to assist you with legal matters related to foreign exchange, taxation, financial planning, and other legal concerns in India.
          </p>
        </div>
      </section>
    </div>
  );
};

export default CompanyIntro;
