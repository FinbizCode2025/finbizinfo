import React, { useEffect } from 'react';

export default function Home() {
  useEffect(() => {
    const hamburgerBtn = document.getElementById("hamburger-btn");
    const mobileMenu = document.getElementById("mobile-menu");
    const closeMenuBtn = document.getElementById("close-menu-btn");
    const mobileMenuLinks = mobileMenu?.querySelectorAll('a');
    const navLinks = document.querySelectorAll('.nav-links a');

    function toggleMobileMenu() {
      mobileMenu?.classList.toggle("hidden");
    }

    hamburgerBtn?.addEventListener("click", toggleMobileMenu);
    closeMenuBtn?.addEventListener("click", toggleMobileMenu);
    mobileMenuLinks?.forEach(link => {
      link.addEventListener('click', toggleMobileMenu);
    });

    function updateActiveNavLink() {
      const sections = document.querySelectorAll('section');
      let currentSectionId = '';
      sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (window.scrollY >= sectionTop - 100 && window.scrollY < sectionTop + sectionHeight - 100) {
          currentSectionId = section.getAttribute('id') || '';
        }
      });

      navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href')?.slice(1) === currentSectionId) {
          link.classList.add('active');
        }
      });
    }

    window.addEventListener('scroll', updateActiveNavLink);

    return () => {
      hamburgerBtn?.removeEventListener("click", toggleMobileMenu);
      closeMenuBtn?.removeEventListener("click", toggleMobileMenu);
      mobileMenuLinks?.forEach(link => {
        link.removeEventListener('click', toggleMobileMenu);
      });
      window.removeEventListener('scroll', updateActiveNavLink);
    };
  }, []);

  return (
    <div className="bg-gray-100">
      <header className="bg-white shadow-md py-4">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <a href="#" className="text-2xl font-bold text-blue-600">A3A Solutions</a>
          <nav className="hidden md:block nav-links">
            <ul className="flex space-x-6">
              <li><a href="#services" className="hover:text-blue-500 transition duration-300">Services</a></li>
              <li><a href="#about" className="hover:text-blue-500 transition duration-300">About Us</a></li>
              <li><a href="#contact" className="hover:text-blue-500 transition duration-300">Contact</a></li>
              <li><a href="#clients" className="hover:text-blue-500 transition duration-300">Clients</a></li>
            </ul>
          </nav>
          <button id="hamburger-btn" className="md:hidden text-gray-600 focus:outline-none" aria-label="Toggle Navigation">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>
        </div>
      </header>

      <div id="mobile-menu" className="hidden fixed top-0 left-0 w-full h-full bg-gray-900 bg-opacity-90 z-50">
        <div className="bg-white w-80 h-full absolute right-0 p-6">
          <div className="flex justify-end mb-4">
            <button id="close-menu-btn" className="text-gray-600 focus:outline-none" aria-label="Close Menu">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <nav>
            <ul className="space-y-4">
              <li><a href="#services" className="block text-lg text-gray-800 hover:text-blue-500 transition duration-300">Services</a></li>
              <li><a href="#about" className="block text-lg text-gray-800 hover:text-blue-500 transition duration-300">About Us</a></li>
              <li><a href="#contact" className="block text-lg text-gray-800 hover:text-blue-500 transition duration-300">Contact</a></li>
              <li><a href="#clients" className="block text-lg text-gray-800 hover:text-blue-500 transition duration-300">Clients</a></li>
            </ul>
          </nav>
        </div>
      </div>

      <section className="bg-gradient-to-br from-blue-100 to-purple-100 py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">Welcome to A3A Solutions</h1>
          <p className="text-lg text-gray-700 mb-8">Your Partner in Digital Transformation</p>
          <button className="bg-blue-600 text-white py-3 px-6 rounded-full hover:bg-blue-700 transition duration-300">Get Started</button>
        </div>
      </section>

      <section id="services" className="py-16">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-gray-800 mb-8">Our Services</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition duration-300">
              <h3 className="text-xl font-semibold text-blue-600 mb-4">Web Development</h3>
              <p className="text-gray-700">We create stunning and responsive websites tailored to your needs.</p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition duration-300">
              <h3 className="text-xl font-semibold text-blue-600 mb-4">Mobile App Development</h3>
              <p className="text-gray-700">We build high-performance mobile apps for iOS and Android.</p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition duration-300">
              <h3 className="text-xl font-semibold text-blue-600 mb-4">Digital Marketing</h3>
              <p className="text-gray-700">We help you reach your target audience and grow your business.</p>
            </div>
          </div>
        </div>
      </section>

      <footer className="bg-gray-800 text-white py-6">
        <div className="container mx-auto px-4 text-center">
          <p>© 2024 A3A Solutions. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}