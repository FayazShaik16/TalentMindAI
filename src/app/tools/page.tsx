'use client';
/* eslint-disable @typescript-eslint/no-explicit-any, react-hooks/set-state-in-effect */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, Sparkles, AlertCircle, BrainCircuit, ShieldCheck, 
  ChevronRight, Terminal, BarChart4, LayoutDashboard, Briefcase, 
  Users, GitCompare, Activity, Settings, User, BookOpen, 
  Download, Send, RefreshCw, Layers, CheckCircle2, X, Search, Check, FileDown, Plus, HelpCircle, FolderOpen
} from 'lucide-react';
import Link from 'next/link';

// Preset Job Descriptions
const PRESETS = [
  {
    id: "cli_test_job_id",
    label: "Senior ML & DevOps Architect",
    text: `Job Title: Senior Software Engineer (AI & DevOps)
Department: Core AI Platforms
Location: Bangalore, India (Hybrid)
We are seeking a senior engineer with 6+ years of experience in modern Python applications.
You will take complete ownership of building container orchestration infrastructure using Kubernetes and Docker.
Responsibilities include mentoring other engineers, designing distributed systems for scalability, and collaborating across product lines.
Key tech stack: Python, Kubernetes, PyTorch, AWS, Docker, Git, Terraform.
Salary: $150,000 - $180,000 yearly.`
  },
  {
    id: "preset_frontend",
    label: "Lead Frontend Engineer",
    text: `Job Title: Lead Frontend Developer
Department: User Interface Engineering
Location: London, UK (Remote)
We are looking for a frontend lead with 5+ years of experience.
You will lead our React design architecture, collaborate with cross-functional designers, and optimize core performance.
Required skills: Typescript, React, CSS, Git, Webpack, Figma.
Preferred: Experience with startup product iterations and mentorship of mid-level developers.`
  }
];

let BACKEND_URL = "https://talentmind-backend.onrender.com";
if (typeof window !== 'undefined') {
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  BACKEND_URL = isLocal ? "http://localhost:8000" : "https://talentmind-backend.onrender.com";
}


// Resilient fetch wrapper — returns null on network errors instead of throwing.
// Prevents console error spam when the backend server is temporarily unavailable.
async function safeFetch(url: string, options?: RequestInit): Promise<Response | null> {
  try {
    return await fetch(url, options);
  } catch {
    // Network error (backend not running) — silently return null
    return null;
  }
}

// Animated Pipeline Stages (11 steps)
const PIPELINE_STAGES = [
  "Reading Job Description",
  "Understanding Role",
  "Extracting Skills",
  "Understanding Responsibilities",
  "Creating Recruiter Intent Profile",
  "Generating Embedding",
  "Searching Candidate Database",
  "Evaluating Candidates",
  "Ranking Candidates",
  "Generating Explanations",
  "Preparing Results"
];

export default function ToolsWorkspace() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'dataset-management' | 'new-session' | 'jobs' | 'rankings' | 'candidates' | 'comparison' | 'analytics' | 'copilot' | 'health' | 'settings'>('dashboard');
  

  // Platform States
  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [jdText, setJdText] = useState(PRESETS[0].text);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [allDbCandidates, setAllDbCandidates] = useState<any[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<any | null>(null);
  const [selectedCompareIds, setSelectedCompareIds] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] = useState<any | null>(null);
  
  // Pipeline & Status
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [pipelineStage, setPipelineStage] = useState<number>(0);
  const [pipelineProgress, setPipelineProgress] = useState<number>(0);
  const [estTimeRemaining, setEstTimeRemaining] = useState<number>(15);
  const [processedCandidatesCount, setProcessedCandidatesCount] = useState<number>(0);
  
  // Recruiter Intent Review States (editable chips)
  const [isReviewingIntent, setIsReviewingIntent] = useState(false);
  const [extractedIntent, setExtractedIntent] = useState<any | null>(null);
  
  // Candidate Search Experience Animation States
  const [isSearchingCandidates, setIsSearchingCandidates] = useState(false);
  const [searchCounters, setSearchCounters] = useState({
    semantic: 0,
    skills: 0,
    experience: 0,
    ranking: 0,
    confidence: 0
  });

  // Telemetry & Stats
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [monitoringData, setMonitoringData] = useState<any>(null);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [jobSessions, setJobSessions] = useState<any[]>([]);
  
  // Drag and drop mock state
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [jdUploadError, setJdUploadError] = useState<string | null>(null);

  // Dataset Management states
  const [datasetStatus, setDatasetStatus] = useState<any>(null);
  const [importHistory, setImportHistory] = useState<any[]>([]);
  const [datasetStats, setDatasetStats] = useState<any>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStats, setUploadStats] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [importProgress, setImportProgress] = useState<any>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadPercentage, setUploadPercentage] = useState<number | null>(null);

  // Candidate Database search/filter states
  const [candSearchQuery, setCandSearchQuery] = useState("");
  const [candFilterSkill, setCandFilterSkill] = useState("");
  const [candFilterExp, setCandFilterExp] = useState("");
  const [candFilterEdu, setCandFilterEdu] = useState("");
  const [candFilterIndustry, setCandFilterIndustry] = useState("");
  const [candPage, setCandPage] = useState(1);
  const [candTotalCount, setCandTotalCount] = useState(0);
  const [candTotalPages, setCandTotalPages] = useState(1);

  // Settings / Preferences
  const [weights, setWeights] = useState<Record<string, number>>({
    semantic: 0.25,
    skills: 0.15,
    career: 0.15,
    projects: 0.10,
    leadership: 0.10,
    potential: 0.10,
    risk: 0.05,
    timeline: 0.10
  });

  // Copilot State
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([
    { role: 'assistant', content: "Hello! I am your AI Recruiter Copilot. Ask me anything about candidate scores, gaps, comparisons, or custom interview guides!" }
  ]);
  const [copilotInput, setCopilotInput] = useState("");
  const [copilotLoading, setCopilotLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Fetch initial dashboard and system status
  const fetchDashboardStats = async () => {
    try {
      const res = await safeFetch(`${BACKEND_URL}/dashboard`);
      if (!res) return;
      const data = await res.json();
      if (data.success) setDashboardData(data.data);
      
      const healthRes = await safeFetch(`${BACKEND_URL}/dashboard/health`);
      if (healthRes) {
        const healthData = await healthRes.json();
        setSystemHealth(healthData.data);
      }

      const sessRes = await safeFetch(`${BACKEND_URL}/dashboard/sessions`);
      if (sessRes) {
        const sessData = await sessRes.json();
        if (sessData.success) setJobSessions(sessData.data);
      }
    } catch (err) {
      console.warn("Backend unavailable — dashboard data will load when server starts.");
    }
  };

  const fetchDbCandidates = async (page = 1, search = "") => {
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "50", search });
      const res = await safeFetch(`${BACKEND_URL}/api/v1/dataset/candidates?${params}`);
      if (res) {
        const json = await res.json();
        if (json.success && json.data) {
          setAllDbCandidates(json.data.candidates || []);
          setCandTotalCount(json.data.total || 0);
          setCandTotalPages(json.data.total_pages || 1);
        }
      }
    } catch (err) {
      console.warn("Backend unavailable — candidates will load when server starts.");
    }
  };

  const fetchRankings = async () => {
    try {
      if (selectedJobId) {
        const rankingRes = await safeFetch(`${BACKEND_URL}/ranking/${selectedJobId}`);
        if (rankingRes) {
          const rankingData = await rankingRes.json();
          if (rankingData.success && rankingData.data) {
            setCandidates(rankingData.data.rankings || []);
          }
        }
      }
    } catch (err) {
      console.warn("Backend unavailable — rankings will load when server starts.");
    }
  };

  const fetchJobsAndCandidates = async () => {
    try {
      // Extended API list jobs
      const jobsRes = await safeFetch(`${BACKEND_URL}/jobs`);
      if (jobsRes) {
        const jobsData = await jobsRes.json();
        if (jobsData.success) setJobs(jobsData.data);
      }

      // Fetch paginated candidates + rankings in parallel (decoupled)
      await Promise.all([fetchDbCandidates(candPage, candSearchQuery), fetchRankings()]);
    } catch (err) {
      console.warn("Backend unavailable — jobs/candidates will load when server starts.");
    }
  };
  const fetchDatasetStatus = async () => {
    try {
      const res = await safeFetch(`${BACKEND_URL}/dataset/status`);
      if (!res) return;
      const data = await res.json();
      if (data.success) {
        setDatasetStatus(data.data.dataset);
        setImportProgress(data.data.progress);
        if (data.data.progress.status === "processing") {
          setIsImporting(true);
        } else {
          setIsImporting(false);
        }
      }
    } catch (err) {
      console.warn("Backend unavailable — dataset status will load when server starts.");
    }
  };

  const fetchDatasetHistory = async () => {
    try {
      const res = await safeFetch(`${BACKEND_URL}/dataset/history`);
      if (!res) return;
      const data = await res.json();
      if (data.success) {
        setImportHistory(data.data);
      }
    } catch (err) {
      console.warn("Backend unavailable — dataset history will load when server starts.");
    }
  };

  const fetchDatasetStats = async () => {
    try {
      const res = await safeFetch(`${BACKEND_URL}/dataset/statistics`);
      if (!res) return;
      const data = await res.json();
      if (data.success) {
        setDatasetStats(data.data);
      }
    } catch (err) {
      console.warn("Backend unavailable — dataset stats will load when server starts.");
    }
  };

  const handleFileSelected = (file: File) => {
    setUploadError(null);
    setUploadStats(null);
    
    // Check format
    const name = file.name.toLowerCase();
    const isJsonlGz = name.endsWith(".jsonl.gz");
    const isJsonl = name.endsWith(".jsonl");
    const isCsv = name.endsWith(".csv");
    
    if (!isJsonl && !isJsonlGz && !isCsv) {
      setUploadError("Unsupported format. Please select a .jsonl, .jsonl.gz, or .csv file.");
      setUploadFile(null);
      return;
    }

    // Check size
    if (file.size > 600 * 1024 * 1024) {
      setUploadError("Maximum file size is 600MB.");
      setUploadFile(null);
      return;
    }

    setUploadFile(file);
    
    // Simple estimation of candidates count by reading part of the file or using size heuristics
    // Let's do a simple size-based guess first, then backend will return exact count
    const estCount = Math.max(1, Math.round(file.size / (isCsv ? 500 : 1500)));
    setUploadStats({
      filename: file.name,
      fileSize: file.size,
      estimatedCandidates: estCount
    });
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;
    setUploadError(null);
    setIsUploading(true);
    setUploadPercentage(0);

    const formData = new FormData();
    formData.append("file", uploadFile);

    try {
      // 1. Upload using XMLHttpRequest to track progress
      const uploadInfo = await new Promise<any>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${BACKEND_URL}/dataset/upload`);
        
        xhr.upload.addEventListener("progress", (event) => {
          if (event.lengthComputable) {
            const pct = Math.round((event.loaded / event.total) * 100);
            setUploadPercentage(pct);
          }
        });

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const resObj = JSON.parse(xhr.responseText);
              resolve(resObj.data);
            } catch (err) {
              reject(new Error("Failed to parse server response"));
            }
          } else {
            try {
              const resObj = JSON.parse(xhr.responseText);
              reject(new Error(resObj.detail || `Upload failed with status ${xhr.status}`));
            } catch {
              reject(new Error(`Upload failed with status ${xhr.status}`));
            }
          }
        };

        xhr.onerror = () => reject(new Error("Network connection error during upload."));
        xhr.send(formData);
      });

      setUploadPercentage(null);
      setIsUploading(false);

      // 2. Import
      const importRes = await fetch(`${BACKEND_URL}/dataset/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filepath: uploadInfo.filepath,
          dataset_name: uploadInfo.filename
        })
      });
      const importData = await importRes.json();
      if (!importRes.ok) {
        throw new Error(importData.detail || "Import failed");
      }

      setIsImporting(true);
      setUploadFile(null);
      setUploadStats(null);
      fetchDatasetStatus();
    } catch (err: any) {
      setUploadPercentage(null);
      setIsUploading(false);
      setUploadError(err.message || "An error occurred during dataset upload.");
    }
  };

  const handleResetDataset = async () => {
    if (!confirm("Are you sure you want to delete all candidates, embeddings, and vector indices? This action is permanent.")) return;
    try {
      const res = await fetch(`${BACKEND_URL}/dataset/reset`, {
        method: "DELETE"
      });
      const data = await res.json();
      if (data.success) {
        alert("Dataset cleared successfully.");
        fetchDatasetStatus();
        fetchDatasetHistory();
        fetchDatasetStats();
        fetchJobsAndCandidates();
      }
    } catch (err) {
      console.error("Failed to reset dataset", err);
    }
  };

  // Re-fetch candidates when page or search changes (server-side pagination)
  useEffect(() => {
    fetchDbCandidates(candPage, candSearchQuery);
  }, [candPage, candSearchQuery]);

  useEffect(() => {
    fetchDashboardStats();
    fetchJobsAndCandidates();
    fetchDatasetStatus();
    fetchDatasetHistory();
    fetchDatasetStats();
  }, [selectedJobId]);

  useEffect(() => {
    let interval: any;
    if (isImporting) {
      interval = setInterval(() => {
        fetchDatasetStatus();
        fetchDatasetHistory();
        fetchDatasetStats();
        fetchDbCandidates(1, "");
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isImporting]);



  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Execute pipeline matcher
  const handleRunPipeline = async () => {
    if (!jdText.trim()) {
      alert("Please paste or upload a Job Description first.");
      return;
    }
    
    setIsAnalyzing(true);
    setPipelineStage(1);
    setPipelineProgress(0);
    setEstTimeRemaining(15);
    setProcessedCandidatesCount(0);
    
    // Simulate pipeline stage progression
    const totalDuration = 12000; // 12 seconds total simulation
    const stageDuration = totalDuration / PIPELINE_STAGES.length;
    
    let currentStage = 1;
    let currentProgress = 0;
    
    const progressInterval = setInterval(() => {
      currentProgress += 1;
      setPipelineProgress(prev => {
        if (prev >= 100) return 100;
        return prev + 1;
      });
      setEstTimeRemaining(prev => {
        if (prev <= 1) return 1;
        return parseFloat((prev - 0.12).toFixed(1) as any);
      });
    }, 120);

    const stageInterval = setInterval(() => {
      currentStage += 1;
      if (currentStage <= PIPELINE_STAGES.length) {
        setPipelineStage(currentStage);
      }
    }, stageDuration);

    const candidateInterval = setInterval(() => {
      setProcessedCandidatesCount(prev => {
        if (prev >= 100000) return 100000;
        return prev + Math.floor(Math.random() * 5000) + 1000;
      });
    }, 150);
    
    try {
      // Call backend JD analyze
      const ingestRes = await fetch(`${BACKEND_URL}/jobs/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_text: jdText })
      });
      const ingested = await ingestRes.json();
      if (!ingested.success) throw new Error("JD ingestion failed.");
      
      const jobId = ingested.data.id;
      setSelectedJobId(jobId);
      
      // Load parsed details into intent review state
      setExtractedIntent({
        id: jobId,
        title: ingested.data.title || "Senior Software Engineer",
        department: ingested.data.department || "Core Engineering",
        seniority: ingested.data.seniority || "Senior",
        experience_required_years: ingested.data.experience_required || 5.0,
        education: ingested.data.intent_profile?.education || ["Bachelor's in Computer Science"],
        primary_skills: ingested.data.intent_profile?.skills?.primary_skills || ["Python", "Docker"],
        secondary_skills: ingested.data.intent_profile?.skills?.secondary_skills || ["AWS", "Git"],
        responsibilities: [
          "Take complete ownership of building container orchestration infrastructure",
          "Design distributed systems for high availability and scalability",
          "Collaborate with engineering managers and product managers"
        ]
      });

      // Finish simulation nicely
      clearInterval(progressInterval);
      clearInterval(stageInterval);
      clearInterval(candidateInterval);
      
      setPipelineStage(PIPELINE_STAGES.length);
      setPipelineProgress(100);
      setEstTimeRemaining(0);
      setProcessedCandidatesCount(100000);
      
      // Delay slightly for premium feel
      setTimeout(() => {
        setIsAnalyzing(false);
        setIsReviewingIntent(true);
      }, 800);
      
    } catch (err) {
      clearInterval(progressInterval);
      clearInterval(stageInterval);
      clearInterval(candidateInterval);
      setIsAnalyzing(false);
      const error = err as any;
      console.error(error);
      alert(error.message || "An error occurred during pipeline execution.");
    }
  };

  // Run final database search and ranking after recruiter intent review
  const handleConfirmAndSearch = async () => {
    setIsReviewingIntent(false);
    setIsSearchingCandidates(true);
    
    // Simulate candidate search counter tick-ups
    const searchInt = setInterval(() => {
      setSearchCounters(prev => {
        const next = { ...prev };
        next.semantic = Math.min(100000, next.semantic + Math.floor(Math.random() * 8000) + 2000);
        next.skills = Math.min(100000, next.skills + Math.floor(Math.random() * 9000) + 3000);
        next.experience = Math.min(100000, next.experience + Math.floor(Math.random() * 10000) + 4000);
        next.ranking = Math.min(100000, next.ranking + Math.floor(Math.random() * 12000) + 5000);
        next.confidence = Math.min(100000, next.confidence + Math.floor(Math.random() * 15000) + 6000);
        return next;
      });
    }, 100);

    try {
      // Call backend ranking execution
      const rankRes = await fetch(`${BACKEND_URL}/ranking/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: selectedJobId, top_k_rerank: 100, weights })
      });
      const ranked = await rankRes.json();
      if (!ranked.success) throw new Error("Ranking matching failed.");

      clearInterval(searchInt);
      setSearchCounters({
        semantic: 100000,
        skills: 100000,
        experience: 100000,
        ranking: 100000,
        confidence: 100000
      });

      setTimeout(async () => {
        setIsSearchingCandidates(false);
        await fetchJobsAndCandidates();
        await fetchDashboardStats();
        setActiveTab('rankings');
      }, 1000);

    } catch (err) {
      clearInterval(searchInt);
      setIsSearchingCandidates(false);
      console.error(err);
      alert("An error occurred during candidate ranking.");
    }
  };

  // Select candidate details
  const handleSelectCandidate = async (candidateId: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/candidate/${candidateId}/explanation?job_id=${selectedJobId}`);
      const data = await res.json();
      if (data.success) {
        setSelectedCandidate(data.data);
      }
    } catch (err) {
      console.error("Failed to load candidate details", err);
    }
  };

  // Compare candidates
  const handleCompareCandidates = async () => {
    if (selectedCompareIds.length < 2) {
      alert("Please select at least 2 candidates to compare.");
      return;
    }
    try {
      const res = await fetch(`${BACKEND_URL}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: selectedJobId, candidate_ids: selectedCompareIds })
      });
      const data = await res.json();
      if (data.success) {
        setComparisonResult(data.data);
        setActiveTab('comparison');
      }
    } catch (err) {
      console.error("Failed to compare candidates", err);
    }
  };

  // Update Settings/Preferences weights
  const handleUpdatePreferences = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/dashboard/preferences`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ranking_weights: weights })
      });
      const data = await res.json();
      if (data.success) {
        alert("Weights updated successfully! Re-run ranking to apply.");
      }
    } catch (err) {
      console.error("Failed to save weights settings", err);
    }
  };

  // AI Copilot Query Assistant
  const handleSendCopilotMessage = async () => {
    if (!copilotInput.trim()) return;
    const query = copilotInput;
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setCopilotInput("");
    setCopilotLoading(true);

    try {
      let aiResponse = "";
      const qLower = query.toLowerCase();

      if (qLower.includes("compare") || qLower.includes("differentiator")) {
        if (candidates.length >= 2) {
          const cid1 = candidates[0].candidate_id;
          const cid2 = candidates[1].candidate_id;
          const res = await fetch(`${BACKEND_URL}/compare`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_id: selectedJobId, candidate_ids: [cid1, cid2] })
          });
          const compData = await res.json();
          if (compData.success && compData.data.decision_intelligence) {
            const di = compData.data.decision_intelligence;
            aiResponse = `Comparing Candidate A (${candidates[0].first_name} ${candidates[0].last_name}) vs Candidate B (${candidates[1].first_name} ${candidates[1].last_name}). Score Gap: ${di.score_gap}%. Primary reasons:\n` + 
              di.differentiators.map((d: string, i: number) => `${i+1}. ${d}`).join("\n");
          } else {
            aiResponse = "I attempted to fetch comparison logs, but no differentiator traces were generated. Ensure rankings are active.";
          }
        } else {
          aiResponse = "I need at least two ranked candidates in this job session to execute a comparison analysis.";
        }
      } else if (qLower.includes("missing") || qLower.includes("gap") || qLower.includes("skills")) {
        if (candidates.length > 0) {
          const topCand = candidates[0];
          const expRes = await fetch(`${BACKEND_URL}/candidate/${topCand.candidate_id}/explanation?job_id=${selectedJobId}`);
          const expData = await expRes.json();
          if (expData.success) {
            const pkg = expData.data;
            const critical = pkg.missing_skills?.critical_missing || [];
            const important = pkg.missing_skills?.important_missing || [];
            aiResponse = `For top candidate ${topCand.first_name} ${topCand.last_name}:\n` + 
              `- Critical Gaps: ${critical.map((c: { name: string; learning_effort: string }) => `${c.name} (${c.learning_effort})`).join(", ") || "None"}\n` +
              `- Important Gaps: ${important.map((c: { name: string; learning_effort: string }) => `${c.name} (${c.learning_effort})`).join(", ") || "None"}`;
          }
        } else {
          aiResponse = "No ranked candidates available to audit missing stack skills.";
        }
      } else if (qLower.includes("health") || qLower.includes("monitoring") || qLower.includes("system")) {
        const monRes = await fetch(`${BACKEND_URL}/dashboard/monitoring`);
        const monData = await monRes.json();
        if (monData.success) {
          const r = monData.data.resources;
          aiResponse = `AI System Health Status:\n` +
            `- CPU Usage: ${r.cpu_usage_percent}%\n` +
            `- Memory Availability: ${r.ram_available_mb} MB (${monData.data.vector_store_health.provider} backend active).`;
        }
      } else {
        if (candidates.length > 0) {
          const topCand = candidates[0];
          const expRes = await fetch(`${BACKEND_URL}/candidate/${topCand.candidate_id}/explanation?job_id=${selectedJobId}`);
          const expData = await expRes.json();
          if (expData.success) {
            aiResponse = `Based on the AI Explainability engine:\n${expData.data.overall_summary}`;
          } else {
            aiResponse = `I see Candidate ${topCand.first_name} ${topCand.last_name} is ranked #1 with match score ${topCand.overall_score}%.`;
          }
        } else {
          aiResponse = "I can help you analyze candidates. Please ingest a Job Description and execute candidate ranking first!";
        }
      }

      setMessages(prev => [...prev, { role: 'assistant', content: aiResponse }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "An error occurred while connecting to the analytics engine." }]);
    } finally {
      setCopilotLoading(false);
    }
  };

  // Format percent numbers
  const formatPercent = (val: string | number | null | undefined) => {
    const num = parseFloat(String(val || 0));
    return isNaN(num) ? "0.0%" : `${num.toFixed(1)}%`;
  };

  const roundSize = (bytes: number) => {
    if (!bytes) return "0 KB";
    if (bytes > 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  // Drag and Drop files handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDatasetDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDatasetDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      handleFileSelected(file);
    }
  };

  const handleJdFileSelected = async (file: File) => {
    setJdUploadError(null);
    const name = file.name.toLowerCase();
    const isTxt = name.endsWith(".txt");
    const isMd = name.endsWith(".md");
    const isPdf = name.endsWith(".pdf");
    const isDocx = name.endsWith(".docx");

    if (!isTxt && !isMd && !isPdf && !isDocx) {
      setJdUploadError("Unsupported file format. Please upload PDF, DOCX, TXT, or MD files.");
      alert("Unsupported file format. Please upload PDF, DOCX, TXT, or MD files.");
      setUploadedFileName(null);
      return;
    }

    setUploadedFileName(file.name);

    if (isTxt || isMd) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          setJdText(event.target.result as string);
        }
      };
      reader.readAsText(file);
    } else {
      // PDF or DOCX file - upload to backend for extraction
      try {
        setJdText("Extracting text from document. Please wait...");
        
        const formData = new FormData();
        formData.append("file", file);
        
        const response = await fetch(`${BACKEND_URL}/jobs/parse-file`, {
          method: "POST",
          body: formData,
        });
        
        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || "Failed to extract text from document.");
        }
        
        const data = await response.json();
        if (data.success && data.data && data.data.text) {
          setJdText(data.data.text);
        } else {
          throw new Error("No text content returned from parser.");
        }
      } catch (err: any) {
        console.error("Error parsing file:", err);
        setJdUploadError(`Failed to parse document: ${err.message || err}`);
        setJdText("");
        setUploadedFileName(null);
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleJdFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleJdFileSelected(e.target.files[0]);
    }
  };

  // Mock Export Shortlist trigger
  const handleExportShortlist = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/dashboard/exports?job_id=${selectedJobId}&format=csv`);
      const data = await res.json();
      if (data.success) {
        alert(`Successfully exported shortlist! Format: Hackathon Submission format (CSV). Path: ${data.data.export_url}`);
      }
    } catch (e) {
      alert("Failed to export candidates list.");
    }
  };

  // Helper chip modification functions
  const handleRemoveChip = (category: string, item: string) => {
    if (!extractedIntent) return;
    setExtractedIntent((prev: any) => ({
      ...prev,
      [category]: prev[category].filter((x: string) => x !== item)
    }));
  };

  const handleAddChip = (category: string, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const target = e.target as HTMLInputElement;
      const val = target.value.trim();
      if (val && extractedIntent) {
        setExtractedIntent((prev: any) => ({
          ...prev,
          [category]: [...prev[category], val]
        }));
        target.value = "";
      }
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-brand-black text-slate-100 font-sans antialiased">
      {/* 1. Left Sidebar Navigation */}
      <aside className="w-64 border-r border-white/[0.06] bg-brand-dark flex flex-col justify-between z-20">
        <div>
          {/* Brand header */}
          <div className="p-6 border-b border-white/[0.06] flex items-center gap-2">
            <BrainCircuit className="h-6 w-6 text-brand-blue animate-pulse" />
            <span className="font-bold tracking-tight text-white text-lg">TalentMind <span className="text-brand-cyan font-mono text-sm">CO-PILOT</span></span>
          </div>

          {/* Nav List */}
          <nav className="p-4 space-y-1">
            <button 
              onClick={() => { setActiveTab('dashboard'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'dashboard' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <LayoutDashboard className="h-4 w-4 text-brand-blue" />
              Dashboard
            </button>
            <button 
              onClick={() => { setActiveTab('dataset-management'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'dataset-management' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <FolderOpen className="h-4 w-4 text-brand-cyan" />
              Add/Manage Candidate Database
            </button>
            <button 
              onClick={() => { setActiveTab('new-session'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'new-session' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <Plus className="h-4 w-4 text-brand-cyan" />
              New Hiring Session
            </button>
            <button 
              onClick={() => { setActiveTab('jobs'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'jobs' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <Briefcase className="h-4 w-4 text-brand-purple" />
              Job Workspace
            </button>
            <button 
              onClick={() => { setActiveTab('rankings'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'rankings' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <Users className="h-4 w-4 text-brand-green" />
              Candidate Rankings
            </button>
            <button 
              onClick={() => { setActiveTab('candidates'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'candidates' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <Layers className="h-4 w-4 text-brand-yellow" />
              Candidate Database
            </button>
            <button 
              onClick={() => { setActiveTab('comparison'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'comparison' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <GitCompare className="h-4 w-4 text-brand-purple" />
              Compare Candidates
            </button>
            <button 
              onClick={() => { setActiveTab('analytics'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'analytics' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <BarChart4 className="h-4 w-4 text-brand-blue" />
              Hiring Analytics
            </button>
            <button 
              onClick={() => { setActiveTab('copilot'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'copilot' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <Sparkles className="h-4 w-4 text-brand-purple" />
              AI Recruiter Copilot
            </button>
            <button 
              onClick={() => { setActiveTab('health'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'health' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <Activity className="h-4 w-4 text-brand-cyan" />
              System Health
            </button>
            <button 
              onClick={() => { setActiveTab('settings'); }}
              className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'settings' ? 'bg-white/[0.06] text-white shadow-inner border border-white/[0.05]' : 'text-slate-400 hover:text-white hover:bg-white/[0.02]'}`}
            >
              <Settings className="h-4 w-4 text-slate-400" />
              Settings
            </button>
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-white/[0.06] space-y-3 bg-brand-black/20">
          <div className="flex items-center gap-3 px-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-slate-400 font-medium">Recruitment Engine Online</span>
          </div>
          <Link href="/" className="block text-center text-xs text-slate-500 hover:text-slate-300">
            Back to Story Landing Page
          </Link>
        </div>
      </aside>

      {/* 2. Main Layout Workspace */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-brand-black relative">
        <header className="h-16 border-b border-white/[0.06] bg-brand-dark/50 flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-4">
            <span className="text-xs text-slate-400 font-mono">Active Hiring Context:</span>
            <select 
              value={selectedJobId} 
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="bg-brand-gray border border-white/[0.08] text-white text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-brand-blue"
            >
              {jobs.map(j => (
                <option key={j.id} value={j.id}>{j.title}</option>
              ))}
              {jobs.length === 0 && <option value="cli_test_job_id">Senior Software Engineer (AI & DevOps)</option>}
            </select>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={async () => {
                await fetchDashboardStats();
                await fetchJobsAndCandidates();
              }}
              className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] text-slate-300 transition-colors"
              title="Sync Stats"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </header>

        {/* Dynamic Views Manager */}
        <div className="flex-1 overflow-y-auto p-8 relative">
          
          {/* PIPELINE OVERLAYS FOR NEW SESSION ANALYSIS */}
          <AnimatePresence>
            {isAnalyzing && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-brand-black/95 z-50 flex flex-col justify-center items-center p-8 overflow-y-auto"
              >
                <div className="max-w-xl w-full space-y-8 text-center">
                  <div className="space-y-3">
                    <div className="flex justify-center mb-4">
                      <div className="relative">
                        <div className="absolute inset-0 rounded-full bg-brand-blue/20 blur-xl animate-pulse" />
                        <BrainCircuit className="h-16 w-16 text-brand-blue animate-pulse relative z-10" />
                      </div>
                    </div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">AI Recruiting Intelligence Active</h2>
                    <p className="text-slate-400 text-xs max-w-sm mx-auto">Deconstructing role description, parsing technology stacks, and structuring recruiter intent maps.</p>
                  </div>

                  {/* Progress Stats */}
                  <div className="grid grid-cols-3 gap-4 bg-white/[0.02] border border-white/[0.06] p-4 rounded-xl text-xs font-mono">
                    <div>
                      <span className="text-slate-500 block">PROGRESS</span>
                      <span className="text-lg font-bold text-white mt-1 block">{pipelineProgress}%</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">EST. REMAINING</span>
                      <span className="text-lg font-bold text-brand-cyan mt-1 block">{estTimeRemaining}s</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">CANDIDATES POOL</span>
                      <span className="text-lg font-bold text-brand-purple mt-1 block">{processedCandidatesCount.toLocaleString()}</span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="h-2 w-full rounded-full bg-brand-dark overflow-hidden border border-white/[0.04]">
                    <div className="h-full bg-gradient-to-r from-brand-blue via-brand-purple to-brand-cyan transition-all duration-150" style={{ width: `${pipelineProgress}%` }} />
                  </div>

                  {/* Sequential Pipeline Stages (11 steps) */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left max-w-md mx-auto">
                    {PIPELINE_STAGES.map((stage, idx) => {
                      const num = idx + 1;
                      const isCompleted = pipelineStage > num;
                      const isActive = pipelineStage === num;
                      
                      return (
                        <div key={idx} className={`flex items-center gap-2 p-2 rounded-lg border transition-all ${
                          isCompleted ? "border-emerald-500/20 bg-emerald-500/5 text-slate-300" :
                          isActive ? "border-brand-blue/30 bg-brand-blue/10 text-white animate-pulse" : "border-transparent text-slate-600"
                        }`}>
                          {isCompleted ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                          ) : isActive ? (
                            <RefreshCw className="h-4 w-4 text-brand-blue animate-spin shrink-0" />
                          ) : (
                            <div className="h-4 w-4 rounded-full border border-slate-700 shrink-0" />
                          )}
                          <span className="text-xs truncate">{stage}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* CANDIDATE DATABASE SEARCH ENGINE LOADING SCREEN */}
          <AnimatePresence>
            {isSearchingCandidates && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-brand-black/95 z-50 flex flex-col justify-center items-center p-8"
              >
                <div className="max-w-md w-full text-center space-y-6">
                  <div className="flex justify-center relative">
                    <div className="absolute inset-0 rounded-full bg-brand-purple/20 blur-xl animate-pulse" />
                    <Sparkles className="h-14 w-14 text-brand-purple animate-bounce relative z-10" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Searching 100,000 Candidates...</h3>
                  <p className="text-slate-400 text-xs">Matching recruiter requirements against technical, professional, and career timeline databases.</p>
                  
                  {/* Processing Sub-Counters */}
                  <div className="space-y-3 bg-white/[0.02] border border-white/[0.06] p-6 rounded-2xl text-left text-xs font-mono">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Semantic Matching Scan</span>
                      <span className="text-white font-bold">{searchCounters.semantic.toLocaleString()} / 100,000</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Skill Profiling Check</span>
                      <span className="text-white font-bold">{searchCounters.skills.toLocaleString()} / 100,000</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Experience Alignment</span>
                      <span className="text-white font-bold">{searchCounters.experience.toLocaleString()} / 100,000</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Decision Index Ranking</span>
                      <span className="text-white font-bold">{searchCounters.ranking.toLocaleString()} / 100,000</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Confidence Calculation</span>
                      <span className="text-white font-bold">{searchCounters.confidence.toLocaleString()} / 100,000</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* RECRUITER INTENT REVIEW VIEW */}
          <AnimatePresence>
            {isReviewingIntent && extractedIntent && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-brand-black/95 z-40 flex flex-col justify-center items-center p-8 overflow-y-auto"
              >
                <div className="max-w-2xl w-full bg-brand-dark border border-white/[0.08] p-8 rounded-3xl space-y-6 shadow-2xl relative">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[10px] font-mono text-brand-blue uppercase tracking-wider block">AI Ingestion Complete</span>
                      <h3 className="text-xl font-bold text-white mt-1">Review Extracted Recruiter Intent</h3>
                    </div>
                    <button onClick={() => setIsReviewingIntent(false)} className="p-1 rounded bg-white/[0.04] text-slate-400 hover:text-white">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  
                  <p className="text-xs text-slate-400 leading-relaxed">
                    The AI parsed the following intent maps from your job description. You can add, remove, or modify items below before running the search.
                  </p>

                  <div className="space-y-4 max-h-[450px] overflow-y-auto pr-2">
                    {/* Role Title */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-mono text-slate-500 block">JOB TITLE</label>
                        <input 
                          type="text" 
                          value={extractedIntent.title} 
                          onChange={(e) => setExtractedIntent({...extractedIntent, title: e.target.value})}
                          className="w-full bg-brand-black border border-white/[0.08] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-blue" 
                        />
                      </div>
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-mono text-slate-500 block">DEPARTMENT</label>
                        <input 
                          type="text" 
                          value={extractedIntent.department} 
                          onChange={(e) => setExtractedIntent({...extractedIntent, department: e.target.value})}
                          className="w-full bg-brand-black border border-white/[0.08] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-blue" 
                        />
                      </div>
                    </div>

                    {/* Experience & Seniority */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-mono text-slate-500 block">EXPERIENCE REQUIRED (YEARS)</label>
                        <input 
                          type="number" 
                          value={extractedIntent.experience_required_years} 
                          onChange={(e) => setExtractedIntent({...extractedIntent, experience_required_years: parseFloat(e.target.value)})}
                          className="w-full bg-brand-black border border-white/[0.08] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-blue" 
                        />
                      </div>
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-mono text-slate-500 block">SENIORITY EXPECTATION</label>
                        <input 
                          type="text" 
                          value={extractedIntent.seniority} 
                          onChange={(e) => setExtractedIntent({...extractedIntent, seniority: e.target.value})}
                          className="w-full bg-brand-black border border-white/[0.08] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-blue" 
                        />
                      </div>
                    </div>

                    {/* Skills editable chips lists */}
                    <div className="space-y-3">
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-mono text-slate-500 block">REQUIRED SKILLS (PRIMARY)</label>
                        <div className="flex flex-wrap gap-1.5 p-2 bg-brand-black rounded-xl border border-white/[0.06]">
                          {extractedIntent.primary_skills.map((skill: string, idx: number) => (
                            <span key={idx} className="inline-flex items-center gap-1 bg-brand-blue/10 border border-brand-blue/20 text-brand-blue text-[10px] font-semibold px-2 py-0.5 rounded">
                              {skill}
                              <button onClick={() => handleRemoveChip('primary_skills', skill)} className="text-brand-blue hover:text-white shrink-0">
                                <X className="h-2.5 w-2.5" />
                              </button>
                            </span>
                          ))}
                          <input 
                            placeholder="Add skill + Enter..."
                            onKeyDown={(e) => handleAddChip('primary_skills', e)}
                            className="bg-transparent text-[10px] text-white focus:outline-none border-none py-0.5 px-1 ml-1"
                          />
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-[10px] font-mono text-slate-500 block">PREFERRED SKILLS (SECONDARY)</label>
                        <div className="flex flex-wrap gap-1.5 p-2 bg-brand-black rounded-xl border border-white/[0.06]">
                          {extractedIntent.secondary_skills.map((skill: string, idx: number) => (
                            <span key={idx} className="inline-flex items-center gap-1 bg-brand-purple/10 border border-brand-purple/20 text-brand-purple text-[10px] font-semibold px-2 py-0.5 rounded">
                              {skill}
                              <button onClick={() => handleRemoveChip('secondary_skills', skill)} className="text-brand-purple hover:text-white shrink-0">
                                <X className="h-2.5 w-2.5" />
                              </button>
                            </span>
                          ))}
                          <input 
                            placeholder="Add skill + Enter..."
                            onKeyDown={(e) => handleAddChip('secondary_skills', e)}
                            className="bg-transparent text-[10px] text-white focus:outline-none border-none py-0.5 px-1 ml-1"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-4 border-t border-white/[0.06] flex justify-end gap-3">
                    <button 
                      onClick={() => setIsReviewingIntent(false)} 
                      className="px-6 py-2.5 rounded-full border border-white/[0.1] hover:bg-white/[0.04] text-xs font-semibold text-slate-300 transition-colors"
                    >
                      Back
                    </button>
                    <button 
                      onClick={handleConfirmAndSearch}
                      className="px-6 py-2.5 rounded-full bg-gradient-to-r from-brand-blue to-brand-purple text-xs font-semibold text-white shadow-lg hover:scale-102 active:scale-98 transition-transform"
                    >
                      Confirm & Search Candidate Pool
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              
              {/* TAB: DATASET MANAGEMENT */}
              {activeTab === 'dataset-management' && (
                <div className="space-y-8">
                  <div>
                    <h3 className="text-xl font-bold tracking-tight text-white font-sans">Add/Manage Candidate Database</h3>
                    <p className="text-xs text-slate-400 mt-1">Upload, process, and vector-index candidate resumes to populate the intelligence database.</p>
                  </div>

                  {/* Top Status Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden bg-brand-dark/40 border border-white/[0.06]">
                      <div className="absolute top-0 right-0 p-4 opacity-10">
                        <FolderOpen className="h-10 w-10 text-brand-cyan" />
                      </div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">Current Dataset Status</span>
                      <h4 className="text-lg font-bold text-white mt-2 truncate">{datasetStatus?.name || "No Dataset Loaded"}</h4>
                      <div className="mt-4 space-y-1 text-xs text-slate-400 font-mono font-semibold">
                        <div className="flex justify-between"><span>Status:</span><span className={datasetStatus?.loaded ? "text-emerald-400 font-bold" : "text-amber-400"}>{datasetStatus?.status || "None"}</span></div>
                        <div className="flex justify-between"><span>Total Candidates:</span><span className="text-white">{datasetStatus?.total_candidates?.toLocaleString() || 0}</span></div>
                        <div className="flex justify-between"><span>Upload Date:</span><span className="text-white">{datasetStatus?.upload_date || "N/A"}</span></div>
                      </div>
                    </div>

                    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden bg-brand-dark/40 border border-white/[0.06]">
                      <div className="absolute top-0 right-0 p-4 opacity-10">
                        <BrainCircuit className="h-10 w-10 text-brand-purple" />
                      </div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">AI Vector Indexing</span>
                      <h4 className="text-lg font-bold text-white mt-2">FAISS Vector Space</h4>
                      <div className="mt-4 space-y-1 text-xs text-slate-400 font-mono font-semibold">
                        <div className="flex justify-between"><span>Embeddings:</span><span className="text-white">{datasetStatus?.embeddings_generated?.toLocaleString() || 0}</span></div>
                        <div className="flex justify-between"><span>FAISS Index:</span><span className={datasetStatus?.vector_index === "Ready" ? "text-emerald-400 font-bold" : "text-slate-500"}>{datasetStatus?.vector_index || "Not Ready"}</span></div>
                        <div className="flex justify-between"><span>Storage Size:</span><span className="text-white">{datasetStatus?.storage_size || "0 KB"}</span></div>
                      </div>
                    </div>

                    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden bg-brand-dark/40 border border-white/[0.06] flex flex-col justify-between">
                      <div>
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">Database Administration</span>
                        <h4 className="text-lg font-bold text-white mt-1">Actions</h4>
                      </div>
                      <div className="mt-4 flex gap-2">
                        {datasetStatus?.loaded && (
                          <button 
                            onClick={handleResetDataset}
                            className="w-full py-2.5 rounded-xl border border-rose-500/20 hover:bg-rose-500/10 text-xs font-semibold text-rose-400 transition-colors"
                          >
                            Delete Dataset & Clear Index
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Upload Component & Live Progress */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="glass-panel p-8 rounded-3xl border border-white/[0.08] lg:col-span-2 space-y-6 bg-brand-dark/30">
                      <div>
                        <h3 className="text-lg font-bold tracking-tight text-white">Upload Dataset</h3>
                        <p className="text-xs text-slate-400 mt-1">Supports JSONL, GZIP (.jsonl.gz), and CSV candidate registry files.</p>
                      </div>

                      {/* Drag & Drop Zone */}
                      {!isImporting && !isUploading && (
                        <div 
                          onDragEnter={handleDatasetDrag}
                          onDragOver={handleDatasetDrag}
                          onDragLeave={handleDatasetDrag}
                          onDrop={handleDatasetDrop}
                          className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
                            dragActive ? "border-brand-blue bg-brand-blue/5" : "border-white/[0.1] hover:border-white/[0.2] bg-brand-black/30"
                          }`}
                        >
                          <input 
                            type="file" 
                            id="dataset-file-upload" 
                            onChange={(e) => {
                              if (e.target.files && e.target.files[0]) handleFileSelected(e.target.files[0]);
                            }}
                            accept=".jsonl,.jsonl.gz,.csv"
                            className="hidden" 
                          />
                          <label htmlFor="dataset-file-upload" className="cursor-pointer space-y-4 block">
                            <div className="flex justify-center">
                              <FolderOpen className="h-12 w-12 text-slate-400 animate-pulse" />
                            </div>
                            <div className="text-sm text-slate-300">
                              {uploadFile ? (
                                <span className="font-bold text-brand-cyan">{uploadFile.name}</span>
                              ) : (
                                <span>Drag & drop dataset file here, or <span className="text-brand-blue underline font-bold">browse</span></span>
                              )}
                            </div>
                            <div className="text-[10px] text-slate-500 font-mono">Maximum file size: 600MB. Supported: .jsonl, .jsonl.gz, .csv</div>
                          </label>
                        </div>
                      )}

                      {/* Upload In-Progress State */}
                      {isUploading && uploadPercentage !== null && (
                        <div className="space-y-4 p-6 bg-white/[0.02] border border-white/[0.06] rounded-2xl">
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-slate-400 font-medium">Uploading dataset file...</span>
                            <span className="text-brand-blue font-bold font-mono">{uploadPercentage}%</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-brand-dark overflow-hidden border border-white/[0.04]">
                            <div 
                              className="h-full bg-gradient-to-r from-brand-blue to-brand-cyan transition-all duration-150" 
                              style={{ width: `${uploadPercentage}%` }} 
                            />
                          </div>
                          <p className="text-[10px] text-slate-500 font-mono">Please keep this tab open until the upload completes.</p>
                        </div>
                      )}

                      {/* Selected File Details & Buttons */}
                      {uploadStats && !isImporting && !isUploading && (
                        <div className="p-4 bg-white/[0.02] border border-white/[0.06] rounded-xl flex justify-between items-center text-xs font-mono">
                          <div className="space-y-1">
                            <div><span className="text-slate-500">File:</span> <span className="text-white">{uploadStats.filename}</span></div>
                            <div><span className="text-slate-500">Size:</span> <span className="text-white">{roundSize(uploadStats.fileSize)}</span></div>
                            <div><span className="text-slate-500">Est. Candidates:</span> <span className="text-white">{uploadStats.estimatedCandidates.toLocaleString()}</span></div>
                          </div>
                          <div className="flex gap-2">
                            <button 
                              onClick={() => { setUploadFile(null); setUploadStats(null); }}
                              className="px-4 py-2 rounded-lg border border-white/[0.08] hover:bg-white/[0.04] text-slate-400 font-semibold"
                            >
                              Cancel
                            </button>
                            <button 
                              onClick={handleFileUpload}
                              className="px-4 py-2 rounded-lg bg-brand-blue hover:scale-102 transition-transform text-white font-semibold flex items-center gap-1.5"
                            >
                              Upload Dataset
                            </button>
                          </div>
                        </div>
                      )}

                      {uploadError && (
                        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-xs flex items-center gap-2">
                          <AlertCircle className="h-4 w-4 shrink-0" />
                          <span>{uploadError}</span>
                        </div>
                      )}

                      {/* Live Processing Pipeline Status */}
                      {isImporting && importProgress && (
                        <div className="space-y-6">
                          <div className="flex justify-between items-start">
                            <div>
                              <h4 className="text-sm font-bold text-white">Pipeline stage: <span className="text-brand-blue">{importProgress.stage_label}...</span></h4>
                              <p className="text-[10px] text-slate-500 font-mono mt-0.5">ACTIVE WORKSPACE INGESTION</p>
                            </div>
                            <span className="px-2 py-0.5 rounded bg-brand-blue/15 text-brand-blue text-[10px] font-bold font-mono">Stage {importProgress.stage}/10</span>
                          </div>

                          {/* Stats Grid */}
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-white/[0.02] border border-white/[0.06] p-4 rounded-xl text-xs font-mono">
                            <div>
                              <span className="text-slate-500 block">PROGRESS</span>
                              <span className="text-base font-bold text-white mt-1 block">{importProgress.progress}%</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">RECORDS</span>
                              <span className="text-base font-bold text-white mt-1 block">{importProgress.current_record.toLocaleString()} / {importProgress.total_records.toLocaleString()}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">ELAPSED TIME</span>
                              <span className="text-base font-bold text-brand-cyan mt-1 block">{importProgress.elapsed_time}s</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">MEMORY USAGE</span>
                              <span className="text-base font-bold text-brand-purple mt-1 block">{importProgress.memory_usage_mb} MB</span>
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div className="h-2 w-full rounded-full bg-brand-dark overflow-hidden border border-white/[0.04]">
                            <div className="h-full bg-gradient-to-r from-brand-blue via-brand-purple to-brand-cyan transition-all duration-150" style={{ width: `${importProgress.progress}%` }} />
                          </div>

                          {/* Pipeline Stages (10 steps) */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => {
                              const labels = {
                                1: "Reading Dataset",
                                2: "Parsing Candidate Records",
                                3: "Validating Records",
                                4: "Cleaning Data",
                                5: "Building Candidate Profiles",
                                6: "Generating Embeddings",
                                7: "Building FAISS Vector Index",
                                8: "Optimizing Search Cache",
                                9: "Saving Metadata",
                                10: "Dataset Ready"
                              };
                              const label = (labels as any)[num];
                              const isCompleted = importProgress.stage > num;
                              const isActive = importProgress.stage === num;
                              
                              return (
                                <div key={num} className={`flex items-center gap-2 p-2.5 rounded-xl border transition-all ${
                                  isCompleted ? "border-emerald-500/20 bg-emerald-500/5 text-slate-300" :
                                  isActive ? "border-brand-blue/30 bg-brand-blue/10 text-white animate-pulse" : "border-transparent text-slate-600"
                                }`}>
                                  {isCompleted ? (
                                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                                  ) : isActive ? (
                                    <RefreshCw className="h-4 w-4 text-brand-blue animate-spin shrink-0" />
                                  ) : (
                                    <div className="h-4 w-4 rounded-full border border-slate-700 shrink-0" />
                                  )}
                                  <span className="text-xs truncate">{label}</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Right column: Post-upload summary / stats */}
                    <div className="glass-panel p-6 rounded-3xl space-y-6 bg-brand-dark/30 flex flex-col justify-between">
                      {datasetStats ? (
                        <div className="space-y-6">
                          <div>
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Post-Ingest Summary</h4>
                            <h3 className="text-lg font-bold text-white mt-1">Dataset Analytics</h3>
                          </div>

                          <div className="space-y-4 text-xs font-mono font-semibold">
                            <div className="flex justify-between border-b border-white/[0.04] pb-2">
                              <span className="text-slate-500">Dataset Name</span>
                              <span className="text-white text-right max-w-[150px] truncate">{datasetStatus?.name}</span>
                            </div>
                            <div className="flex justify-between border-b border-white/[0.04] pb-2">
                              <span className="text-slate-500">Total Candidates</span>
                              <span className="text-white">{datasetStats.total_candidates?.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between border-b border-white/[0.04] pb-2">
                              <span className="text-slate-500">Unique Skills Stack</span>
                              <span className="text-white">{datasetStats.unique_skills_count?.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between border-b border-white/[0.04] pb-2">
                              <span className="text-slate-500">Average Experience</span>
                              <span className="text-white">{datasetStats.average_experience} Years</span>
                            </div>
                          </div>

                          {/* Education distribution chart */}
                          <div className="space-y-3">
                            <h5 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">Education Degrees</h5>
                            <div className="space-y-2">
                              {Object.keys(datasetStats.education_distribution || {}).map((level) => {
                                const count = datasetStats.education_distribution[level];
                                const pct = datasetStats.total_candidates > 0 ? (count / datasetStats.total_candidates) * 100 : 0;
                                return (
                                  <div key={level} className="space-y-1">
                                    <div className="flex justify-between text-[10px] font-mono">
                                      <span className="text-slate-400 truncate max-w-[120px]">{level}</span>
                                      <span className="text-white font-bold">{count.toLocaleString()} ({pct.toFixed(0)}%)</span>
                                    </div>
                                    <div className="h-1.5 w-full rounded-full bg-brand-black overflow-hidden">
                                      <div className="h-full bg-brand-cyan" style={{ width: `${pct}%` }} />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="h-full flex flex-col justify-center items-center text-center text-slate-500 p-6 space-y-3">
                          <Briefcase className="h-8 w-8 text-slate-600 animate-pulse" />
                          <p className="text-xs">No active dataset statistics loaded. Complete a dataset import to view database profiles analytics.</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Recent Imports History Section */}
                  <div className="glass-panel p-6 rounded-3xl space-y-4">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Recent Imports Log</h4>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="text-slate-500 border-b border-white/[0.06]">
                            <th className="pb-3 font-semibold font-mono">FILENAME</th>
                            <th className="pb-3 font-semibold font-mono">FILE SIZE</th>
                            <th className="pb-3 font-semibold font-mono">SUCCESS / TOTAL RECORDS</th>
                            <th className="pb-3 font-semibold font-mono">DURATION</th>
                            <th className="pb-3 font-semibold font-mono">IMPORT DATE</th>
                            <th className="pb-3 font-semibold font-mono">STATUS</th>
                          </tr>
                        </thead>
                        <tbody>
                          {importHistory.map((h) => (
                            <tr key={h.id} className="border-b border-white/[0.04] text-slate-300">
                              <td className="py-3 font-medium text-white">{h.filename}</td>
                              <td className="py-3 font-mono">{roundSize(h.file_size)}</td>
                              <td className="py-3 font-mono text-slate-400">{h.successful_records.toLocaleString()} / {h.total_records.toLocaleString()}</td>
                              <td className="py-3 font-mono text-brand-blue">{h.duration_sec}s</td>
                              <td className="py-3 text-slate-500">{h.created_at}</td>
                              <td className="py-3">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                  h.status === "success" ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/15 text-rose-400"
                                }`}>
                                  {h.status.toUpperCase()}
                                </span>
                              </td>
                            </tr>
                          ))}
                          {importHistory.length === 0 && (
                            <tr>
                              <td colSpan={6} className="py-6 text-center text-slate-500 font-mono">No import history found.</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 1: RECRUITER DASHBOARD */}
              {activeTab === 'dashboard' && (
                <div className="space-y-8">
                  {/* Hero Dashboard Section */}
                  <div className="glass-panel p-8 rounded-3xl border border-white/[0.08] relative overflow-hidden bg-gradient-to-br from-brand-dark to-brand-black/90">
                    <div className="absolute -top-12 -right-12 h-64 w-64 bg-brand-blue/10 rounded-full blur-3xl" />
                    <div className="relative z-10 space-y-4 max-w-lg">
                      <span className="px-3 py-1 rounded-full bg-brand-blue/15 text-brand-blue text-[10px] font-bold tracking-wider uppercase font-mono">System Ready & Active</span>
                      <h2 className="text-3xl font-extrabold tracking-tight text-white leading-tight">Where Intelligence Meets Talent</h2>
                      <p className="text-slate-400 text-sm leading-relaxed">Create structured hiring sessions, import job specifications, and search a database of 100,000 candidate profiles using local semantic models.</p>
                      <button 
                        onClick={() => setActiveTab('new-session')}
                        className="rounded-full bg-gradient-to-r from-brand-blue to-brand-purple px-6 py-3 text-xs font-bold text-white hover:scale-102 transition-transform shadow-lg shadow-brand-blue/20 flex items-center gap-2"
                      >
                        <Plus className="h-4 w-4" />
                        Create New Hiring Session
                      </button>
                    </div>
                  </div>

                  {/* Recruiter Metrics Widgets */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-6 opacity-10">
                        <Users className="h-12 w-12 text-brand-purple" />
                      </div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">CANDIDATES REVIEWED</span>
                      <h3 className="text-3xl font-bold text-white mt-2">{dashboardData?.total_candidates ?? 0}</h3>
                    </div>
                    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-6 opacity-10">
                        <Briefcase className="h-12 w-12 text-brand-blue" />
                      </div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">JOBS CREATED</span>
                      <h3 className="text-3xl font-bold text-white mt-2">{dashboardData?.total_jobs ?? 0}</h3>
                    </div>
                    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-6 opacity-10">
                        <ShieldCheck className="h-12 w-12 text-brand-cyan" />
                      </div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">AVG MATCH CONFIDENCE</span>
                      <h3 className="text-3xl font-bold text-white mt-2">{dashboardData?.avg_confidence !== undefined ? `${dashboardData.avg_confidence}%` : "0.0%"}</h3>
                    </div>
                    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
                      <div className="absolute top-0 right-0 p-6 opacity-10">
                        <FileText className="h-12 w-12 text-brand-green" />
                      </div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">RECENT EXPORTS</span>
                      <h3 className="text-3xl font-bold text-white mt-2">{dashboardData?.activity_metrics?.exports ?? 0}</h3>
                    </div>
                  </div>

                  {/* Recent Hiring Sessions snaps */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="glass-panel p-6 rounded-2xl lg:col-span-2 space-y-4">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Recent Hiring Sessions Snapshots</h4>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="text-slate-500 border-b border-white/[0.06]">
                              <th className="pb-3 font-semibold font-mono">SESSION ID</th>
                              <th className="pb-3 font-semibold font-mono">JOB CONFIG</th>
                              <th className="pb-3 font-semibold font-mono">MATCH SCORE</th>
                              <th className="pb-3 font-semibold font-mono">DATE SNAPSHOT</th>
                            </tr>
                          </thead>
                          <tbody>
                            {jobSessions.slice(0, 5).map((s, idx) => (
                              <tr key={idx} className="border-b border-white/[0.04] text-slate-300">
                                <td className="py-3 font-mono text-slate-200">{s.session_id.substring(0, 8)}...</td>
                                <td className="py-3 text-slate-400 truncate max-w-[120px]">{s.job_id}</td>
                                <td className="py-3 font-semibold text-brand-blue">
                                  v{s.ranking_version}
                                </td>
                                <td className="py-3 text-slate-500">{new Date(s.created_at).toLocaleDateString()}</td>
                              </tr>
                            ))}
                            {jobSessions.length === 0 && (
                              <tr>
                                <td colSpan={4} className="py-4 text-center text-slate-500">No active snapshots recorded. Start a new session.</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Quick Actions Panel */}
                    <div className="glass-panel p-6 rounded-2xl space-y-4 flex flex-col justify-between">
                      <div>
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono mb-4">Quick Recruiter Actions</h4>
                        <div className="space-y-2">
                          <button 
                            onClick={() => setActiveTab('new-session')}
                            className="w-full text-left px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.05] text-xs font-medium text-slate-300 transition-colors flex items-center justify-between"
                          >
                            New Hiring Session
                            <ChevronRight className="h-4 w-4 text-slate-500" />
                          </button>
                          <button 
                            onClick={() => setActiveTab('rankings')}
                            className="w-full text-left px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.05] text-xs font-medium text-slate-300 transition-colors flex items-center justify-between"
                          >
                            Explore Candidate Shortlists
                            <ChevronRight className="h-4 w-4 text-slate-500" />
                          </button>
                          <button 
                            onClick={() => setActiveTab('health')}
                            className="w-full text-left px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.05] text-xs font-medium text-slate-300 transition-colors flex items-center justify-between"
                          >
                            Check System Integrity
                            <ChevronRight className="h-4 w-4 text-slate-500" />
                          </button>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono mt-4">
                        <Check className="h-3.5 w-3.5 text-emerald-500" />
                        All AI pipelines connected & ready.
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: NEW HIRING SESSION */}
              {activeTab === 'new-session' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  <div className="glass-panel p-8 rounded-3xl border border-white/[0.08] lg:col-span-2 space-y-6">
                    <div>
                      <h3 className="text-xl font-bold tracking-tight text-white">Create New Hiring Session</h3>
                      <p className="text-xs text-slate-400 mt-1">Upload a job specification file or paste the details to parse the intent requirements.</p>
                    </div>

                    {/* Drag and Drop area */}
                    <div 
                      onDragEnter={handleDrag}
                      onDragOver={handleDrag}
                      onDragLeave={handleDrag}
                      onDrop={handleDrop}
                      className={`relative border-2 border-dashed rounded-2xl p-6 text-center transition-all ${
                        dragActive ? "border-brand-blue bg-brand-blue/5" : "border-white/[0.1] hover:border-white/[0.2] bg-brand-black/30"
                      }`}
                    >
                      <input 
                        type="file" 
                        id="file-upload" 
                        multiple={false} 
                        onChange={handleFileChange}
                        accept=".txt,.md,.pdf,.docx"
                        className="hidden" 
                      />
                      <label htmlFor="file-upload" className="cursor-pointer space-y-3 block">
                        <div className="flex justify-center">
                          <FileText className="h-10 w-10 text-slate-400 animate-pulse" />
                        </div>
                        <div className="text-xs text-slate-300">
                          {uploadedFileName ? (
                            <span className="font-bold text-brand-cyan">{uploadedFileName}</span>
                          ) : (
                            <span>Drag & drop candidate requirements file, or <span className="text-brand-blue underline font-bold">browse</span></span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">Supported formats: PDF, DOCX, TXT, MD</div>
                      </label>
                    </div>

                    {jdUploadError && (
                      <div className="flex items-center gap-2 bg-rose-500/10 border border-rose-500/20 p-3 rounded-2xl text-xs text-rose-400 font-semibold">
                        <AlertCircle className="h-4 w-4 shrink-0" />
                        <span>{jdUploadError}</span>
                      </div>
                    )}

                    {/* Text Area */}
                    <div className="space-y-2">
                      <label className="text-[10px] font-mono text-slate-400">PASTE JOB DESCRIPTION</label>
                      <textarea
                        value={jdText}
                        onChange={(e) => setJdText(e.target.value)}
                        placeholder="Paste job details title, description, skills and role responsibilities here..."
                        className="w-full h-64 bg-brand-black border border-white/[0.08] rounded-2xl p-4 text-xs text-slate-200 focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/20"
                      />
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                      <button 
                        onClick={() => { setJdText(""); setUploadedFileName(null); setJdUploadError(null); }}
                        className="px-5 py-2.5 rounded-full border border-white/[0.08] hover:bg-white/[0.03] text-xs font-semibold text-slate-400"
                      >
                        Clear
                      </button>
                      <button 
                        onClick={() => setActiveTab('dashboard')}
                        className="px-5 py-2.5 rounded-full border border-white/[0.08] hover:bg-white/[0.03] text-xs font-semibold text-slate-400"
                      >
                        Cancel
                      </button>
                      {!(datasetStatus?.loaded || candTotalCount > 0) ? (
                        <div className="flex flex-col sm:flex-row items-center gap-3 bg-rose-500/10 border border-rose-500/20 p-4 rounded-2xl w-full justify-between text-xs">
                          <div className="flex items-center gap-2 text-rose-400 font-semibold">
                            <AlertCircle className="h-4 w-4 shrink-0" />
                            <span>No candidate dataset available.</span>
                          </div>
                          <button 
                            onClick={() => setActiveTab('dataset-management')}
                            className="px-4 py-2 bg-brand-blue hover:scale-102 transition-transform text-white font-bold rounded-full"
                          >
                            Add Candidate Database
                          </button>
                        </div>
                      ) : (
                        <button 
                          onClick={handleRunPipeline}
                          className="px-6 py-2.5 rounded-full bg-gradient-to-r from-brand-blue to-brand-purple text-xs font-semibold text-white hover:scale-102 transition-transform shadow-lg shadow-brand-blue/15"
                        >
                          Analyze with AI
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Sidebar Guidelines */}
                  <div className="glass-panel p-6 rounded-3xl space-y-6">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Hiring Guide</h4>
                    <div className="space-y-4 text-xs text-slate-400 leading-relaxed">
                      <div className="flex gap-3">
                        <div className="h-5 w-5 rounded-full bg-brand-blue/10 flex items-center justify-center shrink-0">
                          <span className="text-brand-blue font-bold">1</span>
                        </div>
                        <p>Upload or paste your raw requirements text. The AI will read through it, structure seniority levels, and classify technical stacks.</p>
                      </div>
                      <div className="flex gap-3">
                        <div className="h-5 w-5 rounded-full bg-brand-purple/10 flex items-center justify-center shrink-0">
                          <span className="text-brand-purple font-bold">2</span>
                        </div>
                        <p>Perform intent auditing. Make adjustments on skills and seniority details before triggering vector matching scans.</p>
                      </div>
                      <div className="flex gap-3">
                        <div className="h-5 w-5 rounded-full bg-brand-cyan/10 flex items-center justify-center shrink-0">
                          <span className="text-brand-cyan font-bold">3</span>
                        </div>
                        <p>Once matching finishes, browse the results ranked by hiring confidence. Download candidate audit reports or export the shortlist.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: JOB WORKSPACE */}
              {activeTab === 'jobs' && (
                <div className="space-y-8">
                  {jobs.map((job) => {
                    if (job.id !== selectedJobId) return null;
                    return (
                      <div key={job.id} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Text representation */}
                        <div className="glass-panel p-8 rounded-3xl lg:col-span-2 space-y-6">
                          <div>
                            <span className="text-[10px] font-mono text-brand-blue uppercase tracking-wider block">Job Profile Detail</span>
                            <h3 className="text-xl font-bold text-white mt-1">{job.title}</h3>
                          </div>
                          
                          <div className="bg-brand-black/30 border border-white/[0.04] p-5 rounded-2xl space-y-3 text-xs text-slate-300 leading-relaxed max-h-[500px] overflow-y-auto">
                            <span className="text-[10px] font-bold text-slate-500 block uppercase font-mono mb-2">Original Raw Text</span>
                            <p className="whitespace-pre-line">{job.raw_text}</p>
                          </div>
                        </div>

                        {/* Intent Graph Stats */}
                        <div className="glass-panel p-6 rounded-3xl space-y-6">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Intent Parsing Confidence</h4>
                          
                          <div className="space-y-4">
                            {Object.keys(job.confidence_scores).map((k) => {
                              const score = job.confidence_scores[k] * 100;
                              return (
                                <div key={k} className="space-y-1.5">
                                  <div className="flex justify-between text-xs font-mono">
                                    <span className="text-slate-400 capitalize">{k.replace('_', ' ')}</span>
                                    <span className="text-white font-bold">{score.toFixed(0)}%</span>
                                  </div>
                                  <div className="h-1.5 w-full rounded-full bg-brand-black">
                                    <div className="h-full bg-brand-cyan" style={{ width: `${score}%` }} />
                                  </div>
                                </div>
                              );
                            })}
                          </div>

                          <div className="pt-4 border-t border-white/[0.06] text-xs space-y-2 text-slate-500">
                            <span className="block font-mono text-[10px]">Job ID: {job.id}</span>
                            <span className="block font-mono text-[10px]">Seniority: {job.seniority || "Not specified"}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {jobs.length === 0 && (
                    <div className="glass-panel p-12 rounded-3xl text-center text-slate-500">
                      <Briefcase className="h-8 w-8 mx-auto text-slate-600 animate-pulse mb-3" />
                      <p className="text-xs">No jobs are created yet. Click on New Hiring Session to get started.</p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 4: CANDIDATE RANKINGS */}
              {activeTab === 'rankings' && (
                <div className="space-y-6">
                  {/* Action controls */}
                  <div className="flex flex-col md:flex-row justify-between items-center gap-4 bg-brand-dark/30 border border-white/[0.05] p-4 rounded-2xl">
                    <div className="flex items-center gap-3">
                      <button 
                        onClick={handleCompareCandidates}
                        disabled={selectedCompareIds.length < 2}
                        className="rounded-full bg-brand-purple/10 border border-brand-purple/20 hover:bg-brand-purple/20 text-xs font-bold px-4 py-2 text-brand-purple flex items-center gap-2 disabled:opacity-30 disabled:pointer-events-none"
                      >
                        <GitCompare className="h-3.5 w-3.5" />
                        Compare Candidates ({selectedCompareIds.length})
                      </button>
                      <a 
                        href={`${BACKEND_URL}/ranking/${selectedJobId}/export-csv`}
                        download
                        className="rounded-full bg-brand-blue/10 border border-brand-blue/20 hover:bg-brand-blue/20 text-xs font-bold px-4 py-2 text-brand-blue flex items-center gap-2 cursor-pointer transition-colors"
                      >
                        <Download className="h-3.5 w-3.5" />
                        Export Shortlist (CSV)
                      </a>
                      <a 
                        href={`${BACKEND_URL}/ranking/${selectedJobId}/export-xlsx`}
                        download
                        className="rounded-full bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 text-xs font-bold px-4 py-2 text-emerald-400 flex items-center gap-2 cursor-pointer transition-colors"
                      >
                        <Download className="h-3.5 w-3.5 text-emerald-400" />
                        Export Shortlist (XLSX)
                      </a>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Table matches */}
                    <div className="glass-panel p-6 rounded-3xl lg:col-span-2 space-y-4">
                      <h3 className="text-sm font-semibold tracking-tight text-white mb-2">Hiring Match Rankings (Top 100)</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="text-slate-500 border-b border-white/[0.06]">
                              <th className="pb-3 font-semibold font-mono">SELECT</th>
                              <th className="pb-3 font-semibold font-mono">RANK / NAME</th>
                              <th className="pb-3 font-semibold font-mono">OVERALL MATCH</th>
                              <th className="pb-3 font-semibold font-mono">CONFIDENCE</th>
                              <th className="pb-3 font-semibold font-mono">RECOMMENDATION</th>
                              <th className="pb-3 font-semibold font-mono">ACTION</th>
                            </tr>
                          </thead>
                          <tbody>
                            {candidates.slice(0, 100).map((c) => {
                              const isChecked = selectedCompareIds.includes(c.candidate_id);
                              return (
                                <tr key={c.candidate_id} className="border-b border-white/[0.04] text-slate-300 hover:bg-white/[0.01] transition-colors">
                                  <td className="py-4">
                                    <input 
                                      type="checkbox"
                                      checked={isChecked}
                                      onChange={() => {
                                        if (isChecked) {
                                          setSelectedCompareIds(prev => prev.filter(id => id !== c.candidate_id));
                                        } else {
                                          setSelectedCompareIds(prev => [...prev, c.candidate_id]);
                                        }
                                      }}
                                      className="rounded bg-brand-gray border-white/[0.08] text-brand-blue focus:ring-0"
                                    />
                                  </td>
                                  <td className="py-4">
                                    <div className="flex items-center gap-3">
                                      <span className="font-mono font-bold text-brand-blue">#{c.rank}</span>
                                      <div>
                                        <span className="font-semibold text-white block">{c.first_name} {c.last_name}</span>
                                        <span className="text-slate-500 text-[10px] font-mono">{c.candidate_id}</span>
                                      </div>
                                    </div>
                                  </td>
                                  <td className="py-4 font-mono font-bold text-white">{formatPercent(c.overall_score)}</td>
                                  <td className="py-4 font-mono">{formatPercent(c.hiring_confidence * 100)}</td>
                                  <td className="py-4">
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                      c.recommendation === "Strong Hire" ? "bg-emerald-500/15 text-emerald-400" :
                                      c.recommendation === "Hire" ? "bg-blue-500/15 text-blue-400" :
                                      c.recommendation === "Interview" ? "bg-amber-500/15 text-amber-400" : "bg-rose-500/15 text-rose-400"
                                    }`}>
                                      {c.recommendation}
                                    </span>
                                  </td>
                                  <td className="py-4">
                                    <button 
                                      onClick={() => handleSelectCandidate(c.candidate_id)}
                                      className="px-3 py-1.5 rounded-lg bg-brand-blue/10 hover:bg-brand-blue/20 text-brand-blue text-[10px] font-semibold transition-colors"
                                    >
                                      Inspect AI Audit
                                    </button>
                                  </td>
                                </tr>
                              );
                            })}
                            {candidates.length === 0 && (
                              <tr>
                                <td colSpan={6} className="py-8 text-center text-slate-500">No ranked candidates found. Run matching from a job position session.</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Detailed info panel */}
                    <div className="lg:col-span-1">
                      {selectedCandidate ? (
                        <div className="glass-panel p-6 rounded-3xl space-y-6 border border-white/[0.08] sticky top-6">
                          <div className="flex justify-between items-start">
                            <div>
                              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Candidate Intelligence Audit</span>
                              <h3 className="text-base font-bold text-white mt-1">ID: {selectedCandidate.candidate_id}</h3>
                            </div>
                            <button 
                              onClick={() => setSelectedCandidate(null)}
                              className="p-1 rounded bg-white/[0.03] hover:bg-white/[0.06] text-slate-400 hover:text-white"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </div>

                          {/* Fit stats */}
                          <div className="grid grid-cols-2 gap-4 text-xs bg-brand-black/30 p-4 rounded-xl border border-white/[0.04]">
                            <div>
                              <span className="text-slate-500 block">Match Score</span>
                              <span className="font-bold text-white mt-1 block">{formatPercent(selectedCandidate.match_percentage)}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">Confidence</span>
                              <span className="font-bold text-white mt-1 block">{formatPercent(selectedCandidate.hiring_confidence * 100)}</span>
                            </div>
                          </div>

                          {/* Narrative Summary */}
                          <div className="space-y-2">
                            <span className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider block">Hiring Narrative Summary</span>
                            <p className="text-xs text-slate-300 leading-relaxed bg-brand-black/30 p-3 rounded-lg border border-white/[0.02]">
                              {selectedCandidate.overall_summary}
                            </p>
                          </div>

                          {/* Strengths list */}
                          <div className="space-y-3">
                            <span className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider block">Key Professional Strengths</span>
                            <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                              {selectedCandidate.strengths.map((s: { name: string; impact: string; evidence: string }, idx: number) => (
                                <div key={idx} className="bg-white/[0.02] border border-white/[0.04] p-3 rounded-xl space-y-1">
                                  <div className="flex justify-between items-center text-xs">
                                    <span className="font-bold text-white">{s.name}</span>
                                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-semibold ${
                                      s.impact === "High" ? "bg-emerald-500/10 text-emerald-400" : "bg-blue-500/10 text-blue-400"
                                    }`}>{s.impact}</span>
                                  </div>
                                  <p className="text-[10px] text-slate-400 leading-relaxed">{s.evidence}</p>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Weaknesses list */}
                          {selectedCandidate.weaknesses && selectedCandidate.weaknesses.length > 0 && (
                            <div className="space-y-3">
                              <span className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider block">Gaps & Risks</span>
                              <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                                {selectedCandidate.weaknesses.map((w: { name: string; severity: string; evidence: string }, idx: number) => (
                                  <div key={idx} className="bg-rose-500/5 border border-rose-500/10 p-3 rounded-xl space-y-1">
                                    <div className="flex justify-between items-center text-xs">
                                      <span className="font-bold text-rose-400">{w.name}</span>
                                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-400 font-semibold">{w.severity}</span>
                                    </div>
                                    <p className="text-[10px] text-rose-400/80 leading-relaxed">{w.evidence}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Report Export Button */}
                          <div className="pt-2 border-t border-white/[0.06] flex gap-2">
                            <a 
                              href={`${BACKEND_URL}/candidate/${selectedCandidate.candidate_id}/report-pdf?job_id=${selectedJobId}`}
                              className="flex items-center justify-center gap-2 w-full rounded-full bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] py-2 text-xs font-semibold text-white transition-colors"
                            >
                              <FileDown className="h-3.5 w-3.5 text-brand-blue" />
                              Download Recruiter Report (PDF)
                            </a>
                          </div>
                        </div>
                      ) : (
                        <div className="glass-panel p-6 rounded-3xl h-96 flex flex-col justify-center items-center text-center text-slate-500 space-y-3 border border-white/[0.04]">
                          <Users className="h-8 w-8 text-slate-600 animate-pulse" />
                          <p className="text-xs">Select a candidate rank to inspect disaggregated match scores, narrative, strengths, and risks.</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 5: CANDIDATE DATABASE */}
              {activeTab === 'candidates' && (() => {
                // Server-side paginated data — allDbCandidates already contains only the current page
                const paginated = allDbCandidates;

                return (
                  <div className="space-y-6">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                      <div>
                        <div className="flex items-center gap-3">
                          <h3 className="text-xl font-bold text-white">Candidates Database Registry</h3>
                          <span className="px-2 py-0.5 rounded bg-brand-cyan/15 text-brand-cyan text-xs font-bold font-mono">
                            {candTotalCount.toLocaleString()} Profiles
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">Browse all candidates stored in the recruiter-intelligence database. Select candidate profiles for detail analytics audits.</p>
                      </div>
                      
                      {/* Explicit button to import/upload candidate database */}
                      <button 
                        onClick={() => setActiveTab('dataset-management')}
                        className="rounded-full bg-brand-cyan hover:scale-102 transition-transform text-xs font-bold px-4 py-2.5 text-white flex items-center gap-2 shadow-lg shadow-brand-cyan/15"
                      >
                        <Plus className="h-4 w-4" />
                        Add Candidate Database
                      </button>
                    </div>

                    {candTotalCount === 0 ? (
                      <div className="glass-panel p-12 rounded-3xl text-center text-slate-500 border border-white/[0.04] space-y-4 max-w-lg mx-auto mt-8">
                        <Users className="h-12 w-12 text-slate-600 animate-pulse mx-auto" />
                        <h4 className="text-sm font-bold text-white">No Candidate Data Available</h4>
                        <p className="text-xs leading-relaxed">Please import and index a candidate database once under Add/Manage Candidate Database to automatically populate the platform registries.</p>
                        <button 
                          onClick={() => setActiveTab('dataset-management')}
                          className="px-6 py-2 bg-brand-blue hover:scale-102 transition-transform text-white font-bold text-xs rounded-full shadow-lg"
                        >
                          Add Candidate Database
                        </button>
                      </div>
                    ) : (
                      <>
                        {/* Search and Filters grid */}
                        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 bg-brand-dark/30 border border-white/[0.05] p-4 rounded-2xl text-xs">
                          <div className="sm:col-span-2 relative">
                            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                            <input 
                              type="text"
                              placeholder="Search candidate name, ID, or location..."
                              value={candSearchQuery}
                              onChange={(e) => { setCandSearchQuery(e.target.value); setCandPage(1); }}
                              onKeyDown={(e) => { if (e.key === 'Enter') fetchDbCandidates(1, candSearchQuery); }}
                              className="w-full bg-brand-black border border-white/[0.08] rounded-xl pl-9 pr-3 py-2 text-white focus:outline-none focus:border-brand-blue font-sans text-xs"
                            />
                          </div>

                          <div>
                            <select
                              value={candFilterExp}
                              onChange={(e) => { setCandFilterExp(e.target.value); setCandPage(1); }}
                              className="w-full bg-brand-black border border-white/[0.08] rounded-xl px-3 py-2 text-slate-300 focus:outline-none focus:border-brand-blue text-xs font-sans"
                            >
                              <option value="">All Experience</option>
                              <option value="junior">Junior (0-2 Yrs)</option>
                              <option value="mid">Mid (3-5 Yrs)</option>
                              <option value="senior">Senior (6-9 Yrs)</option>
                              <option value="lead">Lead (10+ Yrs)</option>
                            </select>
                          </div>

                          <div>
                            <select
                              value={candFilterEdu}
                              onChange={(e) => { setCandFilterEdu(e.target.value); setCandPage(1); }}
                              className="w-full bg-brand-black border border-white/[0.08] rounded-xl px-3 py-2 text-slate-300 focus:outline-none focus:border-brand-blue text-xs font-sans"
                            >
                              <option value="">All Education</option>
                              <option value="bachelor">Bachelor&apos;s</option>
                              <option value="master">Master&apos;s</option>
                              <option value="phd">PhD</option>
                            </select>
                          </div>

                          <div>
                            <input 
                              type="text"
                              placeholder="Filter by skill..."
                              value={candFilterSkill}
                              onChange={(e) => { setCandFilterSkill(e.target.value); setCandPage(1); }}
                              className="w-full bg-brand-black border border-white/[0.08] rounded-xl px-3 py-2 text-white focus:outline-none focus:border-brand-blue text-xs font-sans"
                            />
                          </div>
                        </div>

                        {/* Candidate database table/list */}
                        <div className="glass-panel p-6 rounded-3xl space-y-4 bg-brand-dark/20 border border-white/[0.06]">
                          <div className="overflow-x-auto max-h-[500px] overflow-y-auto pr-1">
                            <table className="w-full text-left text-xs">
                              <thead className="sticky top-0 bg-brand-dark/90 backdrop-blur z-10">
                                <tr className="text-slate-500 border-b border-white/[0.06]">
                                  <th className="pb-3 font-semibold font-mono">CANDIDATE ID</th>
                                  <th className="pb-3 font-semibold font-mono">NAME</th>
                                  <th className="pb-3 font-semibold font-mono">LOCATION</th>
                                  <th className="pb-3 font-semibold font-mono">YEARS EXPERIENCE</th>
                                  <th className="pb-3 font-semibold font-mono">EDUCATION LEVEL</th>
                                  <th className="pb-3 font-semibold font-mono">PRIMARY STACK</th>
                                  <th className="pb-3 font-semibold font-mono">ACTION</th>
                                </tr>
                              </thead>
                              <tbody>
                                {paginated.map((c) => (
                                  <tr key={c.id} className="border-b border-white/[0.04] text-slate-300 hover:bg-white/[0.01] transition-colors">
                                    <td className="py-4 font-mono text-slate-400">{c.id}</td>
                                    <td className="py-4 font-semibold text-white">{c.first_name} {c.last_name}</td>
                                    <td className="py-4 text-slate-400">{c.location || "Unknown"}</td>
                                    <td className="py-4 font-mono">{c.years_experience} Yrs</td>
                                    <td className="py-4 text-slate-400">{c.education || "N/A"}</td>
                                    <td className="py-4">
                                      <div className="flex gap-1 max-w-[200px] overflow-hidden truncate">
                                        {c.skills.slice(0, 3).map((s: string, i: number) => (
                                          <span key={i} className="px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] text-[9px] text-slate-400 font-semibold shrink-0">
                                            {s}
                                          </span>
                                        ))}
                                        {c.skills.length > 3 && <span className="text-[10px] text-slate-500 shrink-0">+{c.skills.length - 3}</span>}
                                      </div>
                                    </td>
                                    <td className="py-4">
                                      <button 
                                        onClick={() => {
                                          handleSelectCandidate(c.id);
                                          // Redirect to Rankings view or open profile detail
                                          // In this platform, rankings contains the detail panel side drawer!
                                          // Let's select it and go to rankings to display details.
                                          setActiveTab('rankings');
                                        }}
                                        className="px-3 py-1.5 rounded-lg bg-brand-blue/10 hover:bg-brand-blue/20 text-brand-blue text-[10px] font-semibold transition-colors"
                                      >
                                        Inspect Profile
                                      </button>
                                    </td>
                                  </tr>
                                ))}
                                {paginated.length === 0 && (
                                  <tr>
                                    <td colSpan={7} className="py-8 text-center text-slate-500">No candidates matched the selected filters.</td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          </div>

                          {/* Pagination controls */}
                          {candTotalPages > 1 && (
                            <div className="flex justify-between items-center pt-4 border-t border-white/[0.04] text-xs font-mono">
                              <span className="text-slate-500">
                                Showing {((candPage - 1) * 50) + 1} - {Math.min(candPage * 50, candTotalCount)} of {candTotalCount.toLocaleString()}
                              </span>
                              <div className="flex gap-2">
                                <button
                                  disabled={candPage === 1}
                                  onClick={() => setCandPage(p => Math.max(1, p - 1))}
                                  className="px-3 py-1.5 rounded bg-white/[0.02] border border-white/[0.06] text-slate-300 disabled:opacity-30 disabled:pointer-events-none hover:bg-white/[0.05]"
                                >
                                  Previous
                                </button>
                                <span className="px-3 py-1.5 text-white bg-white/[0.04] border border-white/[0.08] rounded">
                                  {candPage} / {candTotalPages.toLocaleString()}
                                </span>
                                <button
                                  disabled={candPage === candTotalPages}
                                  onClick={() => setCandPage(p => Math.min(candTotalPages, p + 1))}
                                  className="px-3 py-1.5 rounded bg-white/[0.02] border border-white/[0.06] text-slate-300 disabled:opacity-30 disabled:pointer-events-none hover:bg-white/[0.05]"
                                >
                                  Next
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                );
              })()}

              {/* TAB 6: CANDIDATE COMPARISON */}
              {activeTab === 'comparison' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-bold tracking-tight text-white">Candidates Comparison Matrix</h3>

                  {comparisonResult ? (
                    <div className="space-y-6">
                      <div className="glass-panel p-6 rounded-3xl overflow-x-auto">
                        <table className="w-full text-left text-xs min-w-[600px]">
                          <thead>
                            <tr className="text-slate-500 border-b border-white/[0.06]">
                              <th className="pb-4 font-semibold font-mono w-1/4">Evaluation Attribute</th>
                              {Object.keys(comparisonResult.comparison).map((cid) => (
                                <th key={cid} className="pb-4 font-semibold font-mono text-white text-center">
                                  {comparisonResult.comparison[cid].name} ({cid})
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            <tr className="border-b border-white/[0.04] text-slate-300">
                              <td className="py-3 font-semibold text-slate-400">Match Percentage</td>
                              {Object.keys(comparisonResult.comparison).map((cid) => (
                                <td key={cid} className="py-3 text-center font-bold text-white">
                                  {formatPercent(comparisonResult.comparison[cid].overall_score)}
                                </td>
                              ))}
                            </tr>
                            <tr className="border-b border-white/[0.04] text-slate-300">
                              <td className="py-3 font-semibold text-slate-400">Hiring Confidence</td>
                              {Object.keys(comparisonResult.comparison).map((cid) => (
                                <td key={cid} className="py-3 text-center font-mono">
                                  {formatPercent(comparisonResult.comparison[cid].hiring_confidence * 100)}
                                </td>
                              ))}
                            </tr>
                            <tr className="border-b border-white/[0.04] text-slate-300">
                              <td className="py-3 font-semibold text-slate-400">Recommendation Status</td>
                              {Object.keys(comparisonResult.comparison).map((cid) => (
                                <td key={cid} className="py-3 text-center">
                                  <span className="px-2 py-0.5 rounded bg-brand-blue/15 text-brand-blue font-semibold">
                                    {comparisonResult.comparison[cid].recommendation}
                                  </span>
                                </td>
                              ))}
                            </tr>
                            <tr className="border-b border-white/[0.04] text-slate-300">
                              <td className="py-3 font-semibold text-slate-400">Semantic Align</td>
                              {Object.keys(comparisonResult.comparison).map((cid) => (
                                <td key={cid} className="py-3 text-center">
                                  {formatPercent(comparisonResult.comparison[cid].scores.semantic_match)}
                                </td>
                              ))}
                            </tr>
                            <tr className="border-b border-white/[0.04] text-slate-300">
                              <td className="py-3 font-semibold text-slate-400">Skills Core Coverage</td>
                              {Object.keys(comparisonResult.comparison).map((cid) => (
                                <td key={cid} className="py-3 text-center">
                                  {formatPercent(comparisonResult.comparison[cid].scores.skills_match)}
                                </td>
                              ))}
                            </tr>
                            <tr className="border-b border-white/[0.04] text-slate-300">
                              <td className="py-3 font-semibold text-slate-400">Leadership Readiness</td>
                              {Object.keys(comparisonResult.comparison).map((cid) => (
                                <td key={cid} className="py-3 text-center">
                                  {formatPercent(comparisonResult.comparison[cid].scores.leadership_match)}
                                </td>
                              ))}
                            </tr>
                            <tr className="border-b border-white/[0.04] text-slate-300">
                              <td className="py-3 font-semibold text-slate-400">Risk Penalty Deductions</td>
                              {Object.keys(comparisonResult.comparison).map((cid) => (
                                <td key={cid} className="py-3 text-center text-rose-400 font-mono">
                                  {comparisonResult.comparison[cid].scores.risk_penalty}%
                                </td>
                              ))}
                            </tr>
                          </tbody>
                        </table>
                      </div>

                      {comparisonResult.decision_intelligence && (
                        <div className="glass-panel p-6 rounded-3xl border border-white/[0.08] space-y-4">
                          <h4 className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
                            <Sparkles className="h-4 w-4 text-brand-purple" />
                            AI Decision Differentiators Summary
                          </h4>
                          <div className="space-y-2">
                            {comparisonResult.decision_intelligence.differentiators.map((d: string, idx: number) => (
                              <div key={idx} className="flex gap-3 text-xs text-slate-300 leading-relaxed">
                                <span className="font-mono text-brand-purple font-bold">#{idx+1}</span>
                                <span>{d}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="glass-panel p-12 rounded-3xl text-center text-slate-500 space-y-3">
                      <GitCompare className="h-10 w-10 mx-auto text-slate-600 animate-pulse mb-3" />
                      <p className="text-xs">Go to Candidate Rankings workspace, check at least two candidates, and click Compare Selected.</p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 7: HIRING ANALYTICS */}
              {activeTab === 'analytics' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-bold tracking-tight text-white">Matching Pool & Skills Analytics</h3>
                    <button 
                      onClick={async () => {
                        const res = await fetch(`${BACKEND_URL}/dashboard/analytics?job_id=${selectedJobId}`);
                        const data = await res.json();
                        if (data.success) setAnalyticsData(data.data);
                      }}
                      className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.06] text-xs text-white transition-all flex items-center gap-2"
                    >
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      Compute Stats
                    </button>
                  </div>

                  {analyticsData ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      {/* Funnel chart */}
                      <div className="glass-panel p-6 rounded-2xl space-y-4">
                        <h4 className="text-sm font-semibold tracking-tight text-white">Recommendations Funnel Distribution</h4>
                        <div className="space-y-3 pt-2">
                          {Object.keys(analyticsData.hiring_funnel.counts).map((rec) => {
                            const count = analyticsData.hiring_funnel.counts[rec];
                            const pct = analyticsData.hiring_funnel.percentages[rec];
                            
                            return (
                              <div key={rec} className="space-y-1.5">
                                <div className="flex justify-between text-xs font-mono">
                                  <span className="text-slate-400">{rec}</span>
                                  <span className="text-white">{count} ({pct}%)</span>
                                </div>
                                <div className="h-2 w-full rounded-full bg-brand-black/50 overflow-hidden">
                                  <div className="h-full bg-brand-blue" style={{ width: `${pct}%` }} />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Top technologies */}
                      <div className="glass-panel p-6 rounded-2xl space-y-4">
                        <h4 className="text-sm font-semibold tracking-tight text-white">Top Candidate Technologies (Frequency)</h4>
                        <div className="space-y-3 pt-2">
                          {analyticsData.top_technologies.slice(0, 5).map((item: { technology: string; count: number }, idx: number) => (
                            <div key={idx} className="flex justify-between items-center text-xs">
                              <span className="font-mono text-slate-300">{item.technology}</span>
                              <div className="flex items-center gap-3 w-2/3 justify-end">
                                <div className="h-2 w-full rounded-full bg-brand-black/50 overflow-hidden max-w-[150px]">
                                  <div className="h-full bg-brand-purple" style={{ width: `${(item.count / analyticsData.total_evaluated) * 100}%` }} />
                                </div>
                                <span className="font-mono text-white">{item.count} profiles</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="glass-panel p-12 rounded-3xl text-center text-slate-500">
                      <BarChart4 className="h-8 w-8 mx-auto text-slate-600 animate-pulse mb-3" />
                      <p className="text-xs">No analytics cached. Click Compute Stats to parse database metrics.</p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 8: AI COPILOT */}
              {activeTab === 'copilot' && (
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 h-[calc(100vh-140px)]">
                  {/* Chat window */}
                  <div className="glass-panel rounded-3xl border border-white/[0.08] lg:col-span-3 flex flex-col justify-between overflow-hidden bg-brand-dark/20 h-full">
                    {/* Header */}
                    <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
                      <span className="text-xs font-bold text-white flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-brand-purple" />
                        AI Recopilot Assistant
                      </span>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-4">
                      {messages.map((m, idx) => (
                        <div key={idx} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider mb-1">
                            {m.role === 'user' ? 'Recruiter' : 'AI Copilot'}
                          </span>
                          <div className={`p-3 rounded-2xl text-xs leading-relaxed max-w-[80%] ${
                            m.role === 'user' ? 'bg-brand-blue text-white rounded-tr-none shadow-lg' : 'bg-white/[0.04] text-slate-300 rounded-tl-none border border-white/[0.03]'
                          }`}>
                            {m.content}
                          </div>
                        </div>
                      ))}
                      {copilotLoading && (
                        <div className="flex flex-col items-start animate-pulse">
                          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider mb-1">AI Copilot</span>
                          <div className="bg-white/[0.04] p-3 rounded-2xl rounded-tl-none border border-white/[0.03] text-xs text-slate-500 flex items-center gap-2">
                            <RefreshCw className="h-3 w-3 animate-spin text-brand-purple" />
                            Evaluating candidate metrics...
                          </div>
                        </div>
                      )}
                      <div ref={chatEndRef} />
                    </div>

                    {/* Input */}
                    <div className="p-4 border-t border-white/[0.06] bg-brand-dark/40 flex items-center gap-2">
                      <input
                        type="text"
                        value={copilotInput}
                        onChange={(e) => setCopilotInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendCopilotMessage()}
                        placeholder="Ask candidate comparison, strengths, gaps, or interview guidelines questions..."
                        className="flex-1 rounded-xl bg-brand-black border border-white/[0.08] px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-blue"
                      />
                      <button 
                        onClick={handleSendCopilotMessage}
                        className="p-2.5 rounded-xl bg-brand-blue text-white hover:scale-105 active:scale-[0.95] transition-transform"
                      >
                        <Send className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Quick templates */}
                  <div className="glass-panel p-6 rounded-3xl space-y-6 h-full">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Quick Inquiries</h4>
                    <div className="space-y-2">
                      <button 
                        onClick={() => { setCopilotInput("Compare top 2 candidates."); }}
                        className="w-full text-left px-3 py-2 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.05] text-xs text-slate-300 transition-colors"
                      >
                        Compare top 2 candidates
                      </button>
                      <button 
                        onClick={() => { setCopilotInput("Show missing skills."); }}
                        className="w-full text-left px-3 py-2 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.05] text-xs text-slate-300 transition-colors"
                      >
                        Auditing missing skills
                      </button>
                      <button 
                        onClick={() => { setCopilotInput("Why is candidate A ranked first?"); }}
                        className="w-full text-left px-3 py-2 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.05] text-xs text-slate-300 transition-colors"
                      >
                        Why is top candidate #1?
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 9: SYSTEM HEALTH (All Engineering Metrices Isolated Here) */}
              {activeTab === 'health' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-bold tracking-tight text-white">System Health & Telemetry Metrics</h3>
                    <button 
                      onClick={async () => {
                        const res = await fetch(`${BACKEND_URL}/dashboard/monitoring`);
                        const data = await res.json();
                        if (data.success) setMonitoringData(data.data);
                      }}
                      className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.06] text-xs text-white transition-all flex items-center gap-2"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                      Fetch Health metrics
                    </button>
                  </div>

                  {/* Dataset Health Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-brand-dark/20 border border-white/[0.05] p-6 rounded-2xl text-xs font-mono">
                    <div className="bg-brand-black/40 border border-white/[0.04] p-4 rounded-xl text-center">
                      <span className="text-[10px] text-slate-500 block">DATASET</span>
                      <span className={`text-sm font-bold mt-2 block ${datasetStatus?.loaded ? "text-emerald-400" : "text-slate-500"}`}>
                        {datasetStatus?.loaded ? "Healthy" : "Not Loaded"}
                      </span>
                    </div>
                    <div className="bg-brand-black/40 border border-white/[0.04] p-4 rounded-xl text-center">
                      <span className="text-[10px] text-slate-500 block">EMBEDDINGS</span>
                      <span className={`text-sm font-bold mt-2 block ${datasetStatus?.embeddings_generated > 0 ? "text-emerald-400" : "text-slate-500"}`}>
                        {datasetStatus?.embeddings_generated > 0 ? "Ready" : "Pending"}
                      </span>
                    </div>
                    <div className="bg-brand-black/40 border border-white/[0.04] p-4 rounded-xl text-center">
                      <span className="text-[10px] text-slate-500 block">FAISS</span>
                      <span className={`text-sm font-bold mt-2 block ${datasetStatus?.vector_index === "Ready" ? "text-emerald-400" : "text-slate-500"}`}>
                        {datasetStatus?.vector_index === "Ready" ? "Ready" : "Pending"}
                      </span>
                    </div>
                    <div className="bg-brand-black/40 border border-white/[0.04] p-4 rounded-xl text-center">
                      <span className="text-[10px] text-slate-500 block">CANDIDATES</span>
                      <span className={`text-sm font-bold mt-2 block ${candTotalCount > 0 ? "text-emerald-400" : "text-slate-500"}`}>
                        {candTotalCount > 0 ? "Loaded" : "0"}
                      </span>
                    </div>
                  </div>

                  {monitoringData ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                      {/* Host Resources */}
                      <div className="glass-panel p-6 rounded-2xl space-y-4 col-span-2">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Hardware Server Telemetry</h4>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-brand-black/40 border border-white/[0.04] p-4 rounded-xl">
                            <span className="text-[10px] text-slate-500 font-mono block">CPU USAGE</span>
                            <span className="text-2xl font-bold text-white mt-1 block">{monitoringData.resources.cpu_usage_percent}%</span>
                          </div>
                          <div className="bg-brand-black/40 border border-white/[0.04] p-4 rounded-xl">
                            <span className="text-[10px] text-slate-500 font-mono block">RAM USAGE</span>
                            <span className="text-2xl font-bold text-white mt-1 block">{monitoringData.resources.ram_usage_percent}%</span>
                          </div>
                          <div className="bg-brand-black/40 border border-white/[0.04] p-4 rounded-xl">
                            <span className="text-[10px] text-slate-500 font-mono block">DISK FREE</span>
                            <span className="text-2xl font-bold text-white mt-1 block">{monitoringData.resources.disk_free_gb} GB</span>
                          </div>
                        </div>
                      </div>

                      {/* FAISS collections statistics */}
                      <div className="glass-panel p-6 rounded-2xl space-y-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">FAISS Vector Database Collections</h4>
                        <div className="space-y-2 max-h-40 overflow-y-auto pr-1 text-xs font-mono">
                          {Object.keys(monitoringData.vector_store_health.collections).map((coll) => {
                            const c = monitoringData.vector_store_health.collections[coll];
                            return (
                              <div key={coll} className="flex justify-between items-center py-1 border-b border-white/[0.02]">
                                <span className="text-slate-400 capitalize">{coll}</span>
                                <span className="text-white font-bold">{c.ntotal} Vectors</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Agents status */}
                      <div className="glass-panel p-6 rounded-2xl space-y-4 col-span-3">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Active Registered AI Agents</h4>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-xs font-mono">
                          {Object.keys(monitoringData.agents_status).map((agent) => {
                            const a = monitoringData.agents_status[agent];
                            return (
                              <div key={agent} className="bg-brand-black/40 border border-white/[0.04] p-4 rounded-xl text-center">
                                <span className="text-[10px] text-slate-400 block truncate">{agent}</span>
                                <span className="text-xs font-bold text-emerald-500 mt-2 block flex items-center justify-center gap-1">
                                  <Check className="h-3 w-3" />
                                  ONLINE
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="glass-panel p-12 rounded-3xl text-center text-slate-500">
                      <Activity className="h-8 w-8 mx-auto text-slate-600 animate-pulse mb-3" />
                      <p className="text-xs">Telemetry stats are offline. Click on Fetch Health metrics to pull database & server resources status.</p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 10: SETTINGS */}
              {activeTab === 'settings' && (
                <div className="glass-panel p-8 rounded-3xl space-y-6 max-w-2xl border border-white/[0.08]">
                  <div>
                    <h3 className="text-lg font-bold tracking-tight text-white">Recruitment Match Scoring Weights</h3>
                    <p className="text-xs text-slate-400 mt-1">Customize weight prioritization parameters for scoring candidate intelligence fits.</p>
                  </div>
                  
                  <div className="space-y-4">
                    {[
                      { name: "semantic", label: "Semantic Core Similarity" },
                      { name: "skills", label: "Skills Stack Coverage" },
                      { name: "career", label: "Career & Tenure Stability" },
                      { name: "projects", label: "Project Depth Rating" },
                      { name: "leadership", label: "Leadership Readiness Index" },
                      { name: "potential", label: "Continuous Upskilling Potential" },
                      { name: "risk", label: "CV Risk Flags Deductions" }
                    ].map((w, idx) => (
                      <div key={idx} className="space-y-2">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="text-slate-300">{w.label}</span>
                          <span className="text-brand-blue font-bold">{(weights[w.name] * 100).toFixed(0)}%</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={weights[w.name] * 100}
                          onChange={(e) => setWeights(prev => ({
                            ...prev,
                            [w.name]: parseFloat((parseInt(e.target.value) / 100).toFixed(2))
                          }))}
                          className="w-full h-1 bg-brand-black rounded-lg appearance-none cursor-pointer accent-brand-blue"
                        />
                      </div>
                    ))}
                  </div>


                  <div className="pt-4 border-t border-white/[0.06] flex justify-end">
                    <button 
                      onClick={handleUpdatePreferences}
                      className="rounded-full bg-brand-blue px-6 py-2.5 text-xs font-semibold text-white shadow-lg hover:scale-102 transition-transform"
                    >
                      Save Preferences Weights
                    </button>
                  </div>
                </div>
              )}

            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
