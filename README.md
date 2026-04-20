# portfolio-tracker
A robust, high-performance financial tracking application designed to manage multiple investment portfolios. This project focuses on real-time data accuracy, currency-aware calculations, and time-series optimization for long-term wealth tracking.

## 💡 Why this exists

Most commercial brokers provide limited statistical insights into long-term performance. This project was born out of the need for a more granular, broker-independent view of financial health. 

Key problems this application solves:
* **Fragmented Portfolios:** Aggregates assets spread across multiple brokers into a single, unified dashboard.
* **Detailed Trade Statistics:** Goes beyond simple "current value" displays by statistically recording every individual trade.
* **Dividend Tracking:** Specifically tracks dividend payouts to provide a complete picture of Total Return, a feature often neglected by standard broker apps.
* **Data Sovereignty:** Enables investors to analyze their data without being tied to a specific broker's interface or limited history.

 ## ✨ Key Features
* **Multi-Portfolio Management:** Create and track separate portfolios (e.g., "Retirement", "Active Trading") with individual base currencies.
* **Automated Live Pricing:** Real-time price fetching for international stocks and ETFs via financial APIs.
* **Time-Series Optimization:** Powered by **TimescaleDB** to handle millions of price points and historical snapshots with ease.
* **Currency Intelligence:** Automatic EUR/USD conversion using live exchange rates, allowing for seamless tracking of international assets.
* **Sophisticated Analytics:** Instant calculation of absolute and relative performance (Profit/Loss), entry value, and current market value.

## 🛠 Tech Stack

### Backend
* **Python & FastAPI:** Chosen for its high performance, asynchronous capabilities, and excellent developer experience with automatic Swagger documentation.
* **TimescaleDB (PostgreSQL):** A specialized time-series database used to efficiently store and query millions of historical price points and portfolio snapshots.
* **SQLAlchemy (ORM):** Provides a robust abstraction layer for database interactions, ensuring type safety and clean data models.
* **Pydantic:** Utilized for rigorous data validation and settings management.
* **JWT (JSON Web Tokens):** Secure, stateless authentication for user accounts.

### Frontend
* **React (Vite):** A modern, fast frontend library for building a responsive and interactive user interface.
* **Tailwind CSS:** For a clean, professional "FinTech" aesthetic and rapid UI development.
* **Lucide React:** Consistent and modern iconography for financial data visualization.

### Data & Tools
* **Financial APIs:** Integrated real-time data fetching for global stocks, ETFs, and FX rates.
* **Decimal Precision:** Use of Python’s `decimal` module and PostgreSQL's `numeric` types to ensure cent-perfect accuracy for all financial calculations.

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Node.js (v18+)
* PostgreSQL with TimescaleDB extension installed

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sinnaj004/portfolio-tracker.git
   cd portfolio-tracker
   ```
2. **Backend Setup:**
   ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
   ```
3. **Frontend Setup:**
   ```bash
    cd ../portfolio-frontend
    npm install
   ```
