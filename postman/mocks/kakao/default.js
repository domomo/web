const http = require("http");
const PORT = process.env.PORT || 4500;
const JSON_HEADER = { "Content-Type": "application/json" };

const server = http.createServer(async (req, res) => {
  const { method, url } = req;
  const body = readForm(req);

  // @endpoint POST /kauth/oauth/token
  if (method === "POST" && url === "/kauth/oauth/token") {
    const form = await body;
    if (form.grant_type !== "authorization_code" || !form.client_id || !form.code) {
      res.writeHead(400, JSON_HEADER);
      return res.end(JSON.stringify({ error: "invalid_request" }));
    }
    res.writeHead(200, JSON_HEADER);
    return res.end(JSON.stringify({ access_token: "simulation-access-token", token_type: "bearer" }));
  }

  // @endpoint GET /kapi/v2/user/me
  if (method === "GET" && url.startsWith("/kapi/v2/user/me?")) {
    if (req.headers.authorization !== "Bearer simulation-access-token") {
      res.writeHead(401, JSON_HEADER);
      return res.end(JSON.stringify({ error: "invalid_token" }));
    }
    const query = new URLSearchParams(url.slice(url.indexOf("?") + 1));
    if (query.get("property_keys") !== '["kakao_account.profile"]') {
      res.writeHead(400, JSON_HEADER);
      return res.end(JSON.stringify({ error: "invalid_property_keys" }));
    }
    res.writeHead(200, JSON_HEADER);
    return res.end(JSON.stringify({
      id: "simulation-user-1",
      kakao_account: { profile: { nickname: "Simulation Nickname" }, email: "ignored@example.com" },
    }));
  }

  res.writeHead(501, JSON_HEADER);
  return res.end(JSON.stringify({ error: "Endpoint not modeled", path: url }));
});

function readForm(req) {
  return new Promise((resolve) => {
    let raw = "";
    req.on("data", (chunk) => { raw += chunk; });
    req.on("end", () => resolve(Object.fromEntries(new URLSearchParams(raw))));
  });
}

server.listen(PORT, () => process.stdout.write(`Kakao simulation mock listening on ${PORT}\n`));
