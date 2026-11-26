// Which junctions can be reached from a start junction by following active one-way roads?
// Breadth-first search: start at "from", follow every road leaving it, then every road
// leaving those junctions, and so on until nothing new is found.
export function reachableFrom(fromId, roads) {
  const start = Number(fromId);
  const seen = new Set([start]);
  const queue = [start];
  while (queue.length) {
    const here = queue.shift();
    for (const road of roads) {
      if (road.is_active && road.from_junction_id === here && !seen.has(road.to_junction_id)) {
        seen.add(road.to_junction_id);
        queue.push(road.to_junction_id);
      }
    }
  }
  seen.delete(start); // you can't travel to where you already are
  return seen;
}
