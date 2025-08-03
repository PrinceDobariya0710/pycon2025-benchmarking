function request()
  local id = math.random(1, 10000)
  return wrk.format("DELETE", "/products/" .. id)
end