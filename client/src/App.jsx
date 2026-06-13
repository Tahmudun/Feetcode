import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import ProblemPage from "./pages/ProblemPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/problems/:id" element={<ProblemPage />} />
      </Routes>
    </BrowserRouter>
  );
}
