import { Routes, Route } from 'react-router-dom'
import Splash from './pages/Splash'
import StrokePredictIntro from './pages/StrokePredictIntro'
import StrokePredict from './pages/StrokePredict'
import MultiStrokePredict from "./pages/MultiStrokePredict"

function App() {
  return (
    <Routes>
      <Route path="/" element={<Splash />} />
      <Route path="/stroke-intro" element={<StrokePredictIntro />} />
      <Route path="/stroke-predict" element={<StrokePredict />} />
      <Route path="/multi-stroke-predict" element={<MultiStrokePredict />} />
    </Routes>
  )
}

export default App
