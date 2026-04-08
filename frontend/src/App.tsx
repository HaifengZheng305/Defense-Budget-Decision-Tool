import ChoroplethMap from "./components/ChoroplethMap";

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>Global Defense Signals Explorer</h1>
        <div className="sub">Hover over a country to see key budget signals</div>
      </header>
      <ChoroplethMap />
    </div>
  );
}
