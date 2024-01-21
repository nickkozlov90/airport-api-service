# airport-api-service

### Introduction
Welcome to the Airport API Service!
This is a Django-based API for tracking flights from airports across the whole globe.

### Airport Service Features
* Public (non-authenticated) users can access all the flights on the platform and filter them by source or destination airport.
* Authenticated users can create orders and book tickets for the flights. They also can access lists of routes, airports, airlines, planes and orders created by themselves. An order can not be created without the tickets.
* Admins can create new instances of all the above-mentioned models and also update information about the flights.
* An icon can be added to the airlines' instances.

### Installation Guide
* Clone this repository [here](https://github.com/nickkozlov90/airport-api-service).
    ```bash
    git clone https://github.com/nickkozlov90/airport-api-service.git
    cd airport-api-service
    ```
* The main branch is the most stable branch at any given time, ensure you're working from it.

* If you want to run the app locally follow the next steps:
2. Create a virtual environment:

    ```bash
   python -m venv venv
    ```
3. Activate the virtual environment:

   On Windows: 
   ```bash
    venv\Scripts\activate
    ```
   On macOS and Linux:
   ```bash
   source venv/bin/activate
   ```
   
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
5. Copy this file ".env_sample" and rename it to ".env", then fill in the actual values for your local development environment.
* Run npm install to install all dependencies
* You can either work with the default mLab database or use your locally installed MongoDB. Do configure to your choice in the application entry file.
* Create an .env file in your project root folder and add your variables. See .env.sample for assistance.