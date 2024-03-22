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
1. Create a virtual environment:

    ```bash
   python -m venv venv
    ```
2. Activate the virtual environment:

   On Windows: 
   ```bash
    venv\Scripts\activate
    ```
   On macOS and Linux:
   ```bash
   source venv/bin/activate
   ```
   
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Copy this file ".env_sample" and rename it to ".env", then fill in the actual values for your local development environment.
5. Apply the migrations:

   ```bash
   python manage.py migrate
   ```

6. To run the development server, use the following command:

   ```bash
   python manage.py runserver
   ```

You can also run the application via the Docker. For this purpose make sure the Docker is installed on your computer and follow the next steps:
1. Fill the actual data for ".env" file (see above).
2. Build the app image and start the containers for the application and the database:
   ```bash
   docker-compose up --build
   ```

Access the application in your web browser at http://localhost:8000.

### API Endpoints

The list of available endpoints you can find at http://127.0.0.1:8000/api/doc/swagger/.


## Project Fixture Files

 - This project includes fixture files that are used for testing and demonstration purposes.
The fixture files contain sample data representing various airplanes, flights, crews and etc.
 - You can find the fixture file is named `data_for_db.json` in the root directory.
 - To load the fixture data into the application, use the following command:

   ```bash
   python manage.py loaddata data_for_db.json
   ```

### Technologies Used
* [Django REST framework](https://www.django-rest-framework.org/) This is toolkit for building Web APIs, providing features such as serialization, authentication, viewsets, and class-based views to simplify the development of RESTful services in Django applications.
* [Docker](https://www.docker.com/) This is a platform that enables developers to automate the deployment and scaling of applications across various computing environments.
* [PostgreSQL](https://www.postgresql.org/) This is a powerful, open source object-relational database system.
* [Swagger](https://swagger.io/) This is open source and professional toolset to simplify documentation of API.

Authentication of users is implemented with means of JSON Web Tokens.