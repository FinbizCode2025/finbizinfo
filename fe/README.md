# FinBizInfo.com

FinBizInfo.com is a financial business information platform designed to provide insights and analysed report to users. The project is built with a backend powered by Python and a react vite frontend to display data in an intuitive way. 

## Project Structure

### Backend:
- **app.py**: The main entry point of the backend application. It serves as the bridge between the frontend and the backend services.
- **backend_files/**: Contains multiple backend files ready to be connected, including API endpoints, database models, and business logic files.

### Frontend:
- The frontend is designed to communicate with the backend and display the data in an easy-to-read format.

## Getting Started

### Prerequisites:
To run the project locally, make sure you have the following installed:
- Python 3.x or above
- pip (Python package installer)
- Virtual environment (optional but recommended)

### Installation:

1. **Clone the repository**:

    ```bash
    git clone https://github.com/_______
    cd _______
    ```

2. **Set up a virtual environment (optional)**:

    If you're using a virtual environment, create and activate it:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use venv\Scripts\activate
    ```

3. **Install dependencies**:

    Make sure to install all the necessary Python packages:

    ```python 
    pip install -r requirements.txt
    ```

4. **Run the app**:

    To start the backend server locally, run:

    ```python
    python app.py
    ```

    This will start the backend server at `http://localhost:5002`.

5. **Connect to the frontend**:

    To start the frontend locally, go to the directory which have package.json and, run:

    ```node
    npm i; npm run dev;
    ```

    This will start the backend server at `http://localhost:5173`.

### Backend API Structure (to be connected):
- **Routes**: These routes are still in development and ready to be connected.
    - `/api/v1/data` - Returns financial business data (Example route).
    - `/api/v1/stats` - Returns business statistics (Example route).

### Next Steps:

**Backend's all files are not properly connected, it is ready to connect,**
**There is total 9 agent available that workings in this project.**
- A1 - Agent to recognise pages (for addressing which pages is have what details, like balance sheet, auditors report, director report or notice) of the uploaded document file.
- A2 - Provide related pages to the individual related routes of backend directly.
- A3 - To calculate financial ratios
- A4 - Analyse compliance Gaps
- A5 - Analyse Auditors Report
- A6 - Analyse Directors Report
- A7 - Create summary for the results made by the last 4 Agents
- A8 - One of the agent has been created for creating vectorization, embedding for the uploaded document file.
- A9 - Added a Chatbot Agent to solve users query related to their uploaded file and our website uses.


All these AI agents have been implement in the code file and available on the root directory of the backend files code, but not connect these files to the main app.py, these files are ready to connect by testing one by one. 

I am working on it, if you want to see the workings of the file, i have added the execution script to the every program's last line.
  
## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

For any issues, feel free to create a GitHub issue or contact the project maintainers.
