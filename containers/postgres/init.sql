-- Create a dedicated database for Keycloak within the same Postgres instance.
-- This runs once on first container start.
CREATE DATABASE keycloak OWNER malaria;
