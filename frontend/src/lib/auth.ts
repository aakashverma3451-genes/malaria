import type { NextAuthOptions } from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";

// KEYCLOAK_ISSUER is browser-reachable (used for the authorization redirect).
// KEYCLOAK_ISSUER_INTERNAL is only reachable from inside the Docker network — used
// for server-to-server calls (token exchange, userinfo, jwks) that this Next.js
// server makes directly, since "localhost" inside this container doesn't resolve
// to the keycloak container. Setting wellKnown to undefined skips NextAuth's
// automatic OIDC discovery (which would otherwise always use the public issuer
// for every endpoint), so each endpoint below can point at the right host.
const publicIssuer = process.env.KEYCLOAK_ISSUER!;
const internalIssuer = process.env.KEYCLOAK_ISSUER_INTERNAL!;

export const authOptions: NextAuthOptions = {
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_ID!,
      clientSecret: process.env.KEYCLOAK_SECRET!,
      issuer: internalIssuer,
      wellKnown: undefined,
      authorization: `${publicIssuer}/protocol/openid-connect/auth`,
      token: `${internalIssuer}/protocol/openid-connect/token`,
      userinfo: `${internalIssuer}/protocol/openid-connect/userinfo`,
      jwks_endpoint: `${internalIssuer}/protocol/openid-connect/certs`,
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.idToken = account.id_token;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
};
