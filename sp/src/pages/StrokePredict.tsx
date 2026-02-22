import React, { useState, useEffect } from 'react';
import './StrokePredict.css';

interface PredictionHistory {
  date: string;
  age: number;
  bmi: number;
  risk_level: string;
  probability: number;
  factors: string[];
  recommendations: string[];
}

interface ApiResponse {
  success: boolean;
  stroke_risk_probability: number;
  risk_level: string;
  risk_color: string;
  risk_score: number;
  bmi: number;
  factors: string[];
  recommendations: string[];
  interpretation: string;
  timestamp: string;
  input_data: {
    age: number;
    bmi: number;
    hypertension: string;
    diabetes: string;
    smoking: string;
    cholesterol: number;
  };
}

interface FormData {
  age: number;
  height: number;
  weight: number;
  hypertension: string;
  diabetes: string;
  smoking: string;
  cholesterol: number;
}

// Export type enum
enum ExportType {
  JSON = 'json',
  CSV = 'csv',
  EXCEL = 'excel',
  WORD = 'word',
  PDF = 'pdf'
}

const StrokePredict = () => {
  const [formData, setFormData] = useState<FormData>({
    age: 0,
    height: 0,
    weight: 0,
    hypertension: 'no',
    diabetes: 'no',
    smoking: 'no',
    cholesterol: 0
  });

  const [result, setResult] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [bmi, setBmi] = useState<number | null>(null);
  const [history, setHistory] = useState<PredictionHistory[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [showExportMenu, setShowExportMenu] = useState<boolean>(false);
  const [exporting, setExporting] = useState<boolean>(false);

  // Load history from localStorage on component mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('stroke_history');
    if (savedHistory) {
      try {
        const parsedHistory = JSON.parse(savedHistory);
        if (Array.isArray(parsedHistory)) {
          setHistory(parsedHistory);
          console.log('Loaded history from localStorage:', parsedHistory.length, 'items');
        } else {
          console.warn('Invalid history format in localStorage');
          setHistory([]);
        }
      } catch (e) {
        console.error('Failed to load history:', e);
        setHistory([]);
      }
    } else {
      console.log('No history found in localStorage');
    }
  }, []);

  // Save history to localStorage whenever it changes
  useEffect(() => {
    if (history.length > 0) {
      localStorage.setItem('stroke_history', JSON.stringify(history));
      console.log('Saved history to localStorage:', history.length, 'items');
    }
  }, [history]);

  const calculateBMI = (weight: number, height: number): number => {
    if (height <= 0) return 0;
    const calculated = weight / ((height / 100) ** 2);
    return parseFloat(calculated.toFixed(1));
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'age' || name === 'height' || name === 'weight' || name === 'cholesterol' 
        ? parseFloat(value) || 0 
        : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setSubmitted(true);

    const { age, height, weight, hypertension, diabetes, smoking, cholesterol } = formData;

    // Validation
    if (age <= 0 || age > 120) {
      setError('Age must be between 1 and 120 years.');
      return;
    }

    if (height <= 0 || height > 300) {
      setError('Height must be between 1 and 300 cm.');
      return;
    }

    if (weight <= 0 || weight > 300) {
      setError('Weight must be between 1 and 300 kg.');
      return;
    }

    if (cholesterol <= 0 || cholesterol > 600) {
      setError('Cholesterol must be between 1 and 600 mg/dL.');
      return;
    }

    // Calculate BMI
    const calculatedBMI = calculateBMI(weight, height);
    setBmi(calculatedBMI);

    setLoading(true);

    try {
      const payload = {
        age,
        height,
        weight,
        hypertension: hypertension === 'yes' ? 1 : 0,
        diabetes: diabetes === 'yes' ? 1 : 0,
        smoking: smoking === 'yes' ? 1 : 0,
        cholesterol
      };

      console.log('Sending payload:', payload);

      const response = await fetch('http://localhost:8000/predict_stroke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const data: ApiResponse = await response.json();

      if (!data.success) {
        throw new Error('API returned unsuccessful response');
      }

      console.log('API response:', data);
      setResult(data);

      // Add to history
      const newHistoryItem: PredictionHistory = {
        date: new Date().toLocaleString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }),
        age,
        bmi: data.bmi || calculatedBMI,
        risk_level: data.risk_level,
        probability: data.stroke_risk_probability,
        factors: data.factors || [],
        recommendations: data.recommendations || []
      };

      // Add to beginning of history and keep last 20 entries
      setHistory(prev => {
        const newHistory = [newHistoryItem, ...prev];
        return newHistory.slice(0, 20);
      });

      console.log('Added to history:', newHistoryItem);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      console.error('Prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all prediction history?')) {
      setHistory([]);
      localStorage.removeItem('stroke_history');
      console.log('History cleared');
    }
  };

  const handleDeleteHistoryItem = (index: number) => {
    if (window.confirm('Delete this prediction from history?')) {
      setHistory(prev => {
        const newHistory = prev.filter((_, i) => i !== index);
        return newHistory;
      });
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'very low': return '#15803d';
      case 'low': return '#10b981';
      case 'moderate': return '#f59e0b';
      case 'high': return '#ea580c';
      case 'very high': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'very low': return '✅';
      case 'low': return '✅';
      case 'moderate': return '⚠️';
      case 'high': return '🚨';
      case 'very high': return '🚨';
      default: return '❓';
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return dateString;
    }
  };

  // ==================== EXPORT FUNCTIONS ====================

  const exportAsJSON = () => {
    const dataStr = JSON.stringify(history, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `stroke-predictions-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const exportAsCSV = () => {
    if (history.length === 0) return;
    
    const headers = ['Date', 'Age', 'BMI', 'Risk Level', 'Probability (%)', 'Factors', 'Recommendations'];
    
    const csvContent = [
      headers.join(','),
      ...history.map(item => [
        `"${item.date}"`,
        item.age,
        item.bmi.toFixed(1),
        `"${item.risk_level}"`,
        (item.probability * 100).toFixed(2),
        `"${item.factors.join('; ')}"`,
        `"${item.recommendations.join('; ')}"`
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `stroke-predictions-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportAsExcel = () => {
    if (history.length === 0) return;
    
    // Create HTML table for Excel
    let html = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" 
            xmlns:x="urn:schemas-microsoft-com:office:excel" 
            xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="UTF-8">
        <title>Stroke Predictions</title>
        <!--[if gte mso 9]>
        <xml>
          <x:ExcelWorkbook>
            <x:ExcelWorksheets>
              <x:ExcelWorksheet>
                <x:Name>Stroke Predictions</x:Name>
                <x:WorksheetOptions>
                  <x:DisplayGridlines/>
                </x:WorksheetOptions>
              </x:ExcelWorksheet>
            </x:ExcelWorksheets>
          </x:ExcelWorkbook>
        </xml>
        <![endif]-->
        <style>
          td { padding: 5px; border: 1px solid #ddd; }
          th { padding: 5px; border: 1px solid #ddd; background-color: #f2f2f2; font-weight: bold; }
        </style>
      </head>
      <body>
        <table>
          <thead>
            <tr>
              <th>Date & Time</th>
              <th>Age</th>
              <th>BMI</th>
              <th>Risk Level</th>
              <th>Probability (%)</th>
              <th>Key Factors</th>
              <th>Recommendations</th>
            </tr>
          </thead>
          <tbody>
    `;
    
    history.forEach(item => {
      html += `
        <tr>
          <td>${item.date}</td>
          <td>${item.age}</td>
          <td>${item.bmi.toFixed(1)}</td>
          <td>${item.risk_level}</td>
          <td>${(item.probability * 100).toFixed(2)}%</td>
          <td>${item.factors.join(', ')}</td>
          <td>${item.recommendations.join(', ')}</td>
        </tr>
      `;
    });
    
    html += `
          </tbody>
        </table>
      </body>
      </html>
    `;
    
    const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `stroke-predictions-${new Date().toISOString().split('T')[0]}.xls`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportAsWord = () => {
    if (history.length === 0) return;
    
    let html = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" 
            xmlns:w="urn:schemas-microsoft-com:office:word" 
            xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="UTF-8">
        <title>Stroke Prediction Report</title>
        <style>
          body { font-family: Arial, sans-serif; }
          h1 { color: #2c3e50; }
          h2 { color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
          table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; font-weight: bold; }
          .risk-low { background-color: #d4edda; color: #155724; }
          .risk-moderate { background-color: #fff3cd; color: #856404; }
          .risk-high { background-color: #f8d7da; color: #721c24; }
          .summary { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; }
        </style>
      </head>
      <body>
        <h1>Stroke Prediction Report</h1>
        <p>Generated on: ${new Date().toLocaleString()}</p>
        <p>Total Predictions: ${history.length}</p>
        
        <div class="summary">
          <h2>Summary Statistics</h2>
          <p>Average Age: ${(history.reduce((sum, item) => sum + item.age, 0) / history.length).toFixed(1)} years</p>
          <p>Average BMI: ${(history.reduce((sum, item) => sum + item.bmi, 0) / history.length).toFixed(1)}</p>
          <p>Risk Distribution: 
            ${(() => {
              const counts = history.reduce((acc, item) => {
                acc[item.risk_level] = (acc[item.risk_level] || 0) + 1;
                return acc;
              }, {} as Record<string, number>);
              return Object.entries(counts).map(([level, count]) => `${level}: ${count}`).join(', ');
            })()}
          </p>
        </div>
        
        <h2>Detailed Prediction History</h2>
        <table>
          <thead>
            <tr>
              <th>Date & Time</th>
              <th>Age</th>
              <th>BMI</th>
              <th>Risk Level</th>
              <th>Probability</th>
              <th>Key Factors</th>
            </tr>
          </thead>
          <tbody>
    `;
    
    history.forEach(item => {
      const riskClass = item.risk_level.toLowerCase().includes('high') ? 'risk-high' : 
                       item.risk_level.toLowerCase().includes('moderate') ? 'risk-moderate' : 'risk-low';
      
      html += `
        <tr>
          <td>${item.date}</td>
          <td>${item.age}</td>
          <td>${item.bmi.toFixed(1)}</td>
          <td class="${riskClass}">${item.risk_level}</td>
          <td>${(item.probability * 100).toFixed(2)}%</td>
          <td>${item.factors.join(', ')}</td>
        </tr>
      `;
    });
    
    html += `
          </tbody>
        </table>
        
        <h2>Recommendations Summary</h2>
        <ul>
    `;
    
    // Collect unique recommendations
    const allRecommendations = history.flatMap(item => item.recommendations);
    const uniqueRecommendations = [...new Set(allRecommendations)];
    
    uniqueRecommendations.forEach(rec => {
      html += `<li>${rec}</li>`;
    });
    
    html += `
        </ul>
        
        <h2>Report Footer</h2>
        <p><em>This report was generated by StrokePredict AI Clinical Assessment Tool.</em></p>
        <p><em>For medical use only. Consult healthcare professionals for interpretation.</em></p>
      </body>
      </html>
    `;
    
    const blob = new Blob(['\ufeff', html], { type: 'application/msword' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `stroke-predictions-report-${new Date().toISOString().split('T')[0]}.doc`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportAsPDF = () => {
    if (history.length === 0) return;
    
    // Create a printable version
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Stroke Predictions Report</title>
        <style>
          @media print {
            @page { margin: 0.5in; }
            body { font-family: Arial, sans-serif; font-size: 12px; }
            h1 { color: #2c3e50; text-align: center; }
            h2 { color: #3498db; border-bottom: 1px solid #3498db; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th, td { border: 1px solid #000; padding: 6px; text-align: left; }
            th { background-color: #f0f0f0; }
            .header { text-align: center; margin-bottom: 20px; }
            .footer { margin-top: 30px; font-size: 10px; color: #666; text-align: center; }
            .risk-badge { padding: 2px 6px; border-radius: 3px; font-weight: bold; }
            .risk-low { background-color: #d4edda; }
            .risk-moderate { background-color: #fff3cd; }
            .risk-high { background-color: #f8d7da; }
          }
          body { font-family: Arial, sans-serif; font-size: 12px; padding: 20px; }
          h1 { color: #2c3e50; text-align: center; }
          h2 { color: #3498db; border-bottom: 1px solid #3498db; }
          table { width: 100%; border-collapse: collapse; margin: 15px 0; }
          th, td { border: 1px solid #000; padding: 6px; text-align: left; }
          th { background-color: #f0f0f0; }
          .header { text-align: center; margin-bottom: 20px; }
          .footer { margin-top: 30px; font-size: 10px; color: #666; text-align: center; }
          .risk-badge { padding: 2px 6px; border-radius: 3px; font-weight: bold; }
          .risk-low { background-color: #d4edda; }
          .risk-moderate { background-color: #fff3cd; }
          .risk-high { background-color: #f8d7da; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>Stroke Prediction Report</h1>
          <p>Generated on: ${new Date().toLocaleString()}</p>
          <p>Total Predictions: ${history.length}</p>
        </div>
        
        <h2>Prediction History</h2>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Age</th>
              <th>BMI</th>
              <th>Risk Level</th>
              <th>Probability</th>
            </tr>
          </thead>
          <tbody>
    `);
    
    history.forEach(item => {
      const riskClass = item.risk_level.toLowerCase().includes('high') ? 'risk-high' : 
                       item.risk_level.toLowerCase().includes('moderate') ? 'risk-moderate' : 'risk-low';
      
      printWindow.document.write(`
        <tr>
          <td>${item.date}</td>
          <td>${item.age}</td>
          <td>${item.bmi.toFixed(1)}</td>
          <td><span class="risk-badge ${riskClass}">${item.risk_level}</span></td>
          <td>${(item.probability * 100).toFixed(2)}%</td>
        </tr>
      `);
    });
    
    printWindow.document.write(`
          </tbody>
        </table>
        
        <h2>Summary Statistics</h2>
        <table>
          <tr>
            <td><strong>Average Age</strong></td>
            <td>${(history.reduce((sum, item) => sum + item.age, 0) / history.length).toFixed(1)} years</td>
          </tr>
          <tr>
            <td><strong>Average BMI</strong></td>
            <td>${(history.reduce((sum, item) => sum + item.bmi, 0) / history.length).toFixed(1)}</td>
          </tr>
          <tr>
            <td><strong>Total Predictions</strong></td>
            <td>${history.length}</td>
          </tr>
        </table>
        
        <div class="footer">
          <p>--- End of Report ---</p>
          <p>StrokePredict AI Clinical Assessment Tool</p>
          <p>For medical use only. Consult healthcare professionals for interpretation.</p>
        </div>
        
        <script>
          window.onload = function() {
            window.print();
            setTimeout(function() {
              window.close();
            }, 1000);
          }
        </script>
      </body>
      </html>
    `);
    
    printWindow.document.close();
  };

  const handleExport = (type: ExportType) => {
    setExporting(true);
    setShowExportMenu(false);
    
    try {
      switch (type) {
        case ExportType.JSON:
          exportAsJSON();
          break;
        case ExportType.CSV:
          exportAsCSV();
          break;
        case ExportType.EXCEL:
          exportAsExcel();
          break;
        case ExportType.WORD:
          exportAsWord();
          break;
        case ExportType.PDF:
          exportAsPDF();
          break;
      }
    } catch (error) {
      console.error('Export error:', error);
      setError('Failed to export file. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  // Calculate statistics for display
  const calculateStatistics = () => {
    if (history.length === 0) return null;
    
    const avgAge = history.reduce((sum, item) => sum + item.age, 0) / history.length;
    const avgBMI = history.reduce((sum, item) => sum + item.bmi, 0) / history.length;
    const avgProbability = history.reduce((sum, item) => sum + item.probability, 0) / history.length;
    
    const riskDistribution = history.reduce((acc, item) => {
      acc[item.risk_level] = (acc[item.risk_level] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    return { avgAge, avgBMI, avgProbability, riskDistribution };
  };

  const stats = calculateStatistics();

  return (
    <div className="stroke-predict-container">
      <div className="stroke-predict-card">
        <div className="stroke-header">
          <div className="stroke-icon">🧠</div>
          <h1>Stroke Risk Predictor</h1>
          <p className="stroke-subtitle">AI-powered clinical risk assessment tool</p>
        </div>

        {error && (
          <div className="stroke-error-alert">
            <span className="error-icon">⚠️</span>
            <span className="error-message">{error}</span>
            <button 
              className="error-dismiss"
              onClick={() => setError('')}
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="stroke-form">
          {/* Form fields remain the same as before */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="age">
                <span className="label-icon">👤</span>
                Age (years)
              </label>
              <input
                type="number"
                id="age"
                name="age"
                value={formData.age || ''}
                onChange={handleInputChange}
                required
                min="1"
                max="120"
                placeholder="Enter age"
              />
              <div className="input-hint">18-120 years</div>
            </div>

            <div className="form-group">
              <label htmlFor="height">
                <span className="label-icon">📏</span>
                Height (cm)
              </label>
              <input
                type="number"
                id="height"
                name="height"
                value={formData.height || ''}
                onChange={handleInputChange}
                required
                step="0.1"
                min="50"
                max="300"
                placeholder="Height in cm"
              />
              <div className="input-hint">50-300 cm</div>
            </div>

            <div className="form-group">
              <label htmlFor="weight">
                <span className="label-icon">⚖️</span>
                Weight (kg)
              </label>
              <input
                type="number"
                id="weight"
                name="weight"
                value={formData.weight || ''}
                onChange={handleInputChange}
                required
                step="0.1"
                min="10"
                max="300"
                placeholder="Weight in kg"
              />
              <div className="input-hint">10-300 kg</div>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="hypertension">
                <span className="label-icon">❤️</span>
                Hypertension
              </label>
              <select
                id="hypertension"
                name="hypertension"
                value={formData.hypertension}
                onChange={handleInputChange}
              >
                <option value="no">No Hypertension</option>
                <option value="yes">Hypertension</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="diabetes">
                <span className="label-icon">🩸</span>
                Diabetes
              </label>
              <select
                id="diabetes"
                name="diabetes"
                value={formData.diabetes}
                onChange={handleInputChange}
              >
                <option value="no">No Diabetes</option>
                <option value="yes">Diabetes</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="smoking">
                <span className="label-icon">🚬</span>
                Smoking Status
              </label>
              <select
                id="smoking"
                name="smoking"
                value={formData.smoking}
                onChange={handleInputChange}
              >
                <option value="no">Non-Smoker</option>
                <option value="yes">Smoker</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cholesterol">
                <span className="label-icon">🧪</span>
                Cholesterol (mg/dL)
              </label>
              <input
                type="number"
                id="cholesterol"
                name="cholesterol"
                value={formData.cholesterol || ''}
                onChange={handleInputChange}
                required
                step="0.1"
                min="100"
                max="600"
                placeholder="Cholesterol level"
              />
              <div className="input-hint">100-600 mg/dL</div>
            </div>
          </div>

          <div className="form-actions">
            <button 
              type="submit" 
              className="predict-button"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="loading-spinner"></span>
                  Processing...
                </>
              ) : (
                <>
                  <span className="button-icon">🔍</span>
                  Predict Stroke Risk
                </>
              )}
            </button>
            
            {history.length > 0 && (
              <button 
                type="button" 
                className="clear-button"
                onClick={handleClearHistory}
              >
                <span className="button-icon">🗑️</span>
                Clear All History
              </button>
            )}
          </div>
        </form>

        {bmi !== null && (
          <div className="bmi-display">
            <h3>Calculated BMI</h3>
            <div className="bmi-value">{bmi.toFixed(1)}</div>
            <p className="bmi-category">
              {bmi < 18.5 ? 'Underweight' : 
               bmi < 25 ? 'Normal' : 
               bmi < 30 ? 'Overweight' : 'Obese'}
            </p>
          </div>
        )}

        {result && (
          <div className="result-container">
            <h2>Prediction Results</h2>
            <div 
              className="risk-card"
              style={{ borderColor: result.risk_color || getRiskColor(result.risk_level) }}
            >
              <div className="risk-header">
                <span className="risk-icon">{getRiskIcon(result.risk_level)}</span>
                <h3>Stroke Risk Assessment</h3>
                <span className="risk-timestamp">{formatDate(result.timestamp)}</span>
              </div>
              
              <div className="risk-details">
                <div className="risk-level">
                  <span className="risk-label">Risk Level:</span>
                  <span 
                    className="risk-value"
                    style={{ color: result.risk_color || getRiskColor(result.risk_level) }}
                  >
                    {result.risk_level}
                  </span>
                </div>
                
                <div className="risk-probability">
                  <span className="risk-label">Probability:</span>
                  <span className="probability-value">
                    {(result.stroke_risk_probability * 100).toFixed(2)}%
                  </span>
                </div>

                <div className="risk-score">
                  <span className="risk-label">Risk Score:</span>
                  <span className="score-value">{result.risk_score}/100</span>
                </div>

                <div className="probability-bar">
                  <div 
                    className="probability-fill"
                    style={{ 
                      width: `${result.stroke_risk_probability * 100}%`,
                      backgroundColor: result.risk_color || getRiskColor(result.risk_level)
                    }}
                  />
                </div>
              </div>

              {result.factors && result.factors.length > 0 && (
                <div className="factors-section">
                  <h4>Key Risk Factors:</h4>
                  <ul className="factors-list">
                    {result.factors.map((factor, index) => (
                      <li key={index} className="factor-item">
                        <span className="factor-icon">•</span>
                        {factor}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.recommendations && result.recommendations.length > 0 && (
                <div className="recommendations">
                  <h4>Recommendations:</h4>
                  <ul>
                    {result.recommendations.map((rec, index) => (
                      <li key={index} className="recommendation-item">
                        <span className="recommendation-icon">→</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="interpretation">
                <p>{result.interpretation}</p>
              </div>
            </div>
          </div>
        )}

        {history.length > 0 && (
          <div className="history-container">
            <div className="history-header">
              <div className="history-title-section">
                <h3>Prediction History</h3>
                <span className="history-count">
                  {history.length} {history.length === 1 ? 'prediction' : 'predictions'}
                </span>
                {stats && (
                  <div className="history-stats">
                    <span className="stat-item">
                      <span className="stat-label">Avg Age:</span>
                      <span className="stat-value">{stats.avgAge.toFixed(1)}</span>
                    </span>
                    <span className="stat-item">
                      <span className="stat-label">Avg BMI:</span>
                      <span className="stat-value">{stats.avgBMI.toFixed(1)}</span>
                    </span>
                  </div>
                )}
              </div>
              <div className="history-controls">
                <div className="export-dropdown">
                  <button 
                    className="history-export-btn"
                    onClick={() => setShowExportMenu(!showExportMenu)}
                    disabled={exporting}
                  >
                    {exporting ? (
                      <>
                        <span className="loading-spinner small"></span>
                        Exporting...
                      </>
                    ) : (
                      <>
                        <span className="button-icon">📥</span>
                        Export
                        <span className="dropdown-arrow">▾</span>
                      </>
                    )}
                  </button>
                  
                  {showExportMenu && (
                    <div className="export-menu">
                      <div className="export-menu-header">
                        <span>Export Format</span>
                        <button 
                          className="close-menu"
                          onClick={() => setShowExportMenu(false)}
                        >
                          ✕
                        </button>
                      </div>
                      <div className="export-options">
                        <button 
                          className="export-option"
                          onClick={() => handleExport(ExportType.JSON)}
                        >
                          <span className="export-icon">📄</span>
                          <div>
                            <div className="export-format">JSON</div>
                            <div className="export-desc">Raw data format</div>
                          </div>
                        </button>
                        <button 
                          className="export-option"
                          onClick={() => handleExport(ExportType.CSV)}
                        >
                          <span className="export-icon">📊</span>
                          <div>
                            <div className="export-format">CSV</div>
                            <div className="export-desc">Spreadsheet data</div>
                          </div>
                        </button>
                        <button 
                          className="export-option"
                          onClick={() => handleExport(ExportType.EXCEL)}
                        >
                          <span className="export-icon">📈</span>
                          <div>
                            <div className="export-format">Excel</div>
                            <div className="export-desc">Microsoft Excel</div>
                          </div>
                        </button>
                        <button 
                          className="export-option"
                          onClick={() => handleExport(ExportType.WORD)}
                        >
                          <span className="export-icon">📝</span>
                          <div>
                            <div className="export-format">Word</div>
                            <div className="export-desc">Formatted report</div>
                          </div>
                        </button>
                        <button 
                          className="export-option"
                          onClick={() => handleExport(ExportType.PDF)}
                        >
                          <span className="export-icon">📄</span>
                          <div>
                            <div className="export-format">PDF</div>
                            <div className="export-desc">Printable document</div>
                          </div>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <div className="history-table-container">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Date & Time</th>
                    <th>Age</th>
                    <th>BMI</th>
                    <th>Risk Level</th>
                    <th>Probability</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item, index) => (
                    <tr key={index} className="history-row">
                      <td className="history-date">{item.date}</td>
                      <td className="history-age">{item.age}</td>
                      <td className="history-bmi">{item.bmi.toFixed(1)}</td>
                      <td className="history-risk">
                        <span 
                          className="risk-badge"
                          style={{ backgroundColor: getRiskColor(item.risk_level) }}
                        >
                          <span className="risk-badge-icon">{getRiskIcon(item.risk_level)}</span>
                          <span className="risk-badge-text">{item.risk_level}</span>
                        </span>
                      </td>
                      <td className="history-probability">
                        <div className="probability-display">
                          <span className="probability-value">{(item.probability * 100).toFixed(2)}%</span>
                          <div className="probability-mini-bar">
                            <div 
                              className="probability-mini-fill"
                              style={{ 
                                width: `${item.probability * 100}%`,
                                backgroundColor: getRiskColor(item.risk_level)
                              }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="history-actions">
                        <button 
                          className="delete-history-btn"
                          onClick={() => handleDeleteHistoryItem(index)}
                          title="Delete this prediction"
                          aria-label="Delete prediction"
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {stats && (
              <div className="statistics-summary">
                <h4>Statistics Summary</h4>
                <div className="stats-grid">
                  <div className="stat-card">
                    <div className="stat-label">Average Age</div>
                    <div className="stat-value">{stats.avgAge.toFixed(1)}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Average BMI</div>
                    <div className="stat-value">{stats.avgBMI.toFixed(1)}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Avg Probability</div>
                    <div className="stat-value">{(stats.avgProbability * 100).toFixed(2)}%</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Risk Distribution</div>
                    <div className="stat-value">
                      {Object.entries(stats.riskDistribution).map(([level, count]) => (
                        <div key={level} className="risk-dist-item">
                          <span className="risk-dot" style={{ backgroundColor: getRiskColor(level) }}></span>
                          {level}: {count}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {!submitted && !loading && history.length === 0 && (
          <div className="info-card">
            <h4>📋 How to Use</h4>
            <p>Enter patient data to get an AI-powered stroke risk prediction based on clinical factors.</p>
            <ul>
              <li><strong>All fields are required</strong> - fill in accurate information</li>
              <li><strong>Height and weight</strong> are used to calculate BMI automatically</li>
              <li><strong>Results are saved locally</strong> - your history persists between sessions</li>
              <li><strong>Export options</strong> - download history in multiple formats (JSON, CSV, Excel, Word, PDF)</li>
              <li><strong>Medical disclaimer</strong> - consult healthcare professionals for medical advice</li>
            </ul>
            <div className="info-note">
              💡 <strong>Tip:</strong> Your prediction history will appear here after your first submission.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StrokePredict;