"""Embedded HTML template for the Optix Dashboard.

Single-page application using Alpine.js for reactivity, Tailwind CSS for styling,
marked.js for markdown rendering, and highlight.js for syntax highlighting.
"""

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en" x-data="{ darkMode: localStorage.getItem('optix-theme') !== 'light' }" :class="darkMode ? 'dark' : ''">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Optix Dashboard</title>
    <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.3/dist/cdn.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked@11.1.1/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/highlight.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github-dark.min.css">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        theme: {
                            bg: 'var(--color-bg)',
                            card: 'var(--color-card)',
                            border: 'var(--color-border)',
                            text: 'var(--color-text)',
                            muted: 'var(--color-muted)',
                            accent: 'var(--color-accent)',
                        }
                    }
                }
            }
        }
    </script>
    <style>
        :root {
            --color-bg: #e2e8f0;
            --color-card: #ffffff;
            --color-border: #bac3d1;
            --color-text: #1e293b;
            --color-muted: #475569;
            --color-accent: #6cd189;
        }
        .dark {
            --color-bg: #0f172a;
            --color-card: #1e293b;
            --color-border: #334155;
            --color-text: #e2e8f0;
            --color-muted: #94a3b8;
            --color-accent: #1a8c42;
        }
        [x-cloak] { display: none !important; }
        .prose pre { margin: 0; }
        .prose code { background: transparent; }

        /* Light mode code block overrides */
        :root:not(.dark) .prose pre,
        :root:not(.dark) .hljs {
            background: #f1f5f9 !important;
            color: #1e293b !important;
        }
        :root:not(.dark) .hljs-keyword,
        :root:not(.dark) .hljs-selector-tag,
        :root:not(.dark) .hljs-built_in,
        :root:not(.dark) .hljs-name,
        :root:not(.dark) .hljs-tag { color: #7c3aed !important; }
        :root:not(.dark) .hljs-string,
        :root:not(.dark) .hljs-attr { color: #059669 !important; }
        :root:not(.dark) .hljs-comment { color: #64748b !important; }
        :root:not(.dark) .hljs-number,
        :root:not(.dark) .hljs-literal { color: #dc2626 !important; }
        :root:not(.dark) .hljs-function,
        :root:not(.dark) .hljs-title { color: #2563eb !important; }
    </style>
</head>
<body class="bg-theme-bg text-theme-text min-h-screen" x-data="dashboard()" x-init="init()">
    <!-- Header -->
    <header class="bg-theme-card border-b border-theme-border sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div class="flex items-center gap-4">
                <h1 class="text-xl font-bold">Optix Dashboard</h1>
                <span class="text-theme-muted text-sm" x-show="projectName" x-text="'• ' + projectName"></span>
                <div class="flex items-center gap-2" x-show="health">
                    <span class="w-2 h-2 rounded-full"
                          :class="{
                              'bg-green-500': health?.status === 'healthy',
                              'bg-yellow-500': health?.status === 'degraded',
                              'bg-red-500': health?.status === 'unhealthy'
                          }"></span>
                    <span class="text-sm text-theme-muted" x-text="health?.status || 'unknown'"></span>
                </div>
            </div>
            <div class="flex items-center gap-4">
                <button @click="activeTab = 'workflows'"
                        :class="activeTab === 'workflows' ? 'bg-theme-accent' : 'bg-theme-border'"
                        class="px-4 py-2 rounded-lg text-sm font-medium transition-opacity hover:opacity-80">
                    Workflows
                </button>
                <button @click="activeTab = 'reports'"
                        :class="activeTab === 'reports' ? 'bg-theme-accent' : 'bg-theme-border'"
                        class="px-4 py-2 rounded-lg text-sm font-medium transition-opacity hover:opacity-80">
                    Reports
                </button>
                <button @click="activeTab = 'debug'"
                        :class="activeTab === 'debug' ? 'bg-theme-accent' : 'bg-theme-border'"
                        class="px-4 py-2 rounded-lg text-sm font-medium transition-opacity hover:opacity-80">
                    Debug
                </button>
                <button @click="toggleTheme()"
                        class="w-10 h-9 rounded-lg text-sm font-medium transition-opacity bg-theme-border hover:opacity-80 flex items-center justify-center"
                        title="Toggle theme">
                    <span x-text="darkMode ? '☀' : '☾'"></span>
                </button>
            </div>
        </div>
    </header>

    <!-- Error Banner -->
    <div x-show="error" x-cloak
         class="bg-red-100 dark:bg-red-900/50 border-b border-red-300 dark:border-red-700 px-4 py-3 text-red-700 dark:text-red-200 text-sm">
        <span x-text="error"></span>
        <button @click="error = null" class="ml-2 text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-200">&times;</button>
    </div>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- Workflows Tab -->
        <div x-show="activeTab === 'workflows'" x-cloak>
            <!-- Active Workflows -->
            <section class="mb-8">
                <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
                    <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    Active Workflows
                    <span class="text-theme-muted text-sm font-normal" x-text="'(' + activeWorkflows.length + ')'"></span>
                </h2>
                <div x-show="activeWorkflows.length === 0" class="bg-theme-card rounded-lg p-8 text-center text-theme-muted">
                    No active workflows
                </div>
                <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <template x-for="workflow in activeWorkflows" :key="workflow.id">
                        <div @click="showWorkflowDetail(workflow.id)"
                             class="bg-theme-card rounded-lg p-4 border border-theme-border hover:border-blue-500 cursor-pointer transition-colors">
                            <div class="flex items-center justify-between mb-2">
                                <span class="font-medium" x-text="formatAuditType(workflow.audit_type)"></span>
                                <span class="text-xs px-2 py-1 rounded-full"
                                      :class="getConfidenceClasses(workflow.confidence)"
                                      x-text="workflow.confidence"></span>
                            </div>
                            <div class="mb-3">
                                <div class="flex justify-between text-xs text-theme-muted mb-1">
                                    <span>Progress</span>
                                    <span x-text="workflow.current_step + '/' + workflow.total_steps"></span>
                                </div>
                                <div class="w-full bg-theme-border rounded-full h-2">
                                    <div class="bg-theme-accent h-2 rounded-full transition-all duration-300"
                                         :style="'width: ' + workflow.progress_percent + '%'"></div>
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </section>

            <!-- Completed Workflows -->
            <section>
                <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
                    <span class="w-2 h-2 bg-gray-500 rounded-full"></span>
                    Completed Workflows
                    <span class="text-theme-muted text-sm font-normal" x-text="'(' + completedWorkflows.length + ')'"></span>
                </h2>
                <div x-show="completedWorkflows.length === 0" class="bg-theme-card rounded-lg p-8 text-center text-theme-muted">
                    No completed workflows
                </div>
                <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <template x-for="workflow in completedWorkflows" :key="workflow.id">
                        <div @click="showWorkflowDetail(workflow.id)"
                             class="bg-theme-card rounded-lg p-4 border border-theme-border hover:border-blue-500 cursor-pointer transition-colors opacity-75">
                            <div class="flex items-center justify-between mb-2">
                                <span class="font-medium" x-text="formatAuditType(workflow.audit_type)"></span>
                                <span class="text-xs px-2 py-1 rounded-full"
                                      :class="getConfidenceClasses(workflow.confidence)"
                                      x-text="workflow.confidence"></span>
                            </div>
                            <div class="mb-3">
                                <div class="flex justify-between text-xs text-theme-muted mb-1">
                                    <span>Completed</span>
                                    <span x-text="workflow.current_step + '/' + workflow.total_steps"></span>
                                </div>
                                <div class="w-full bg-theme-border rounded-full h-2">
                                    <div class="bg-green-600 h-2 rounded-full"
                                         :style="'width: ' + workflow.progress_percent + '%'"></div>
                                </div>
                            </div>
                            <div class="flex items-center justify-between text-xs text-theme-muted">
                                <span x-text="workflow.findings_count + ' findings'"></span>
                                <span x-text="formatTime(workflow.updated_at)"></span>
                            </div>
                        </div>
                    </template>
                </div>
            </section>
        </div>

        <!-- Reports Tab -->
        <div x-show="activeTab === 'reports'" x-cloak>
            <h2 class="text-lg font-semibold mb-4">Generated Reports</h2>

            <!-- Filter Bar -->
            <div class="flex flex-wrap gap-2 mb-4">
                <template x-for="filterType in ['all', 'Security', 'A11y', 'DevOps', 'Principal']" :key="filterType">
                    <button @click="reportFilter = filterType"
                            :class="reportFilter === filterType ? 'bg-theme-accent' : 'bg-theme-border hover:bg-theme-border/80'"
                            class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                        <span x-text="filterType === 'all' ? 'All' : filterType"></span>
                        <span class="bg-theme-bg/50 px-1.5 py-0.5 rounded text-xs"
                              x-text="reportCountByType(filterType)"></span>
                    </button>
                </template>
            </div>

            <div x-show="filteredReports.length === 0" class="bg-theme-card rounded-lg p-8 text-center text-theme-muted">
                <span x-text="reportFilter === 'all' ? 'No reports available' : 'No ' + reportFilter + ' reports found'"></span>
            </div>
            <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <template x-for="report in filteredReports" :key="report.filename">
                    <div @click="showReport(report.filename)"
                         class="bg-theme-card rounded-lg p-4 border border-theme-border hover:border-blue-500 cursor-pointer transition-colors">
                        <div class="flex items-center justify-between mb-2">
                            <span class="font-medium truncate" x-text="report.filename"></span>
                        </div>
                        <div class="flex items-center gap-2 mb-2">
                            <span class="text-xs px-2 py-1 bg-theme-border rounded-full" x-text="report.audit_type"></span>
                            <span class="text-xs text-theme-muted" x-text="report.size_formatted"></span>
                        </div>
                        <div class="text-xs text-theme-muted" x-text="formatTime(report.created_at)"></div>
                    </div>
                </template>
            </div>
        </div>

        <!-- Debug Tab -->
        <div x-show="activeTab === 'debug'" x-cloak>
            <h2 class="text-lg font-semibold mb-4">Workflow Debug Inspector</h2>
            <div class="bg-theme-card rounded-lg p-4 border border-theme-border">
                <div class="flex gap-4 mb-3">
                    <input type="text"
                           x-model="debugWorkflowId"
                           placeholder="Enter workflow UUID..."
                           class="flex-1 bg-theme-bg border border-theme-border rounded-lg px-4 py-2 text-theme-text placeholder-theme-muted focus:outline-none focus:border-blue-500">
                    <button @click="fetchDebugState()"
                            :disabled="!debugWorkflowId"
                            class="bg-theme-accent hover:opacity-90 disabled:bg-theme-border disabled:cursor-not-allowed px-6 py-2 rounded-lg font-medium transition-colors">
                        Fetch
                    </button>
                </div>
                <div x-show="debugError" class="bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 rounded-lg p-3 mb-3 text-red-700 dark:text-red-200 text-sm">
                    <span x-text="debugError"></span>
                </div>
                <div x-show="debugState" class="relative">
                    <button @click="copyDebugState()"
                            class="absolute top-2 right-6 bg-theme-border hover:bg-theme-muted/30 px-3 py-1 rounded text-xs font-medium transition-colors">
                        Copy
                    </button>
                    <pre class="bg-theme-bg border border-theme-border rounded-lg p-4 overflow-x-auto text-sm max-h-[55vh] overflow-y-auto"><code x-text="JSON.stringify(debugState, null, 2)"></code></pre>
                </div>
                <div x-show="!debugState && !debugError" class="text-center text-theme-muted py-4">
                    Enter a workflow UUID and click Fetch to inspect raw state
                </div>
            </div>
        </div>
    </main>

    <!-- Workflow Detail Modal -->
    <div x-show="selectedWorkflow" x-cloak
         @keydown.escape.window="selectedWorkflow = null"
         class="fixed inset-0 z-50 overflow-y-auto">
        <div class="fixed inset-0 bg-black/50" @click="selectedWorkflow = null"></div>
        <div class="relative min-h-screen flex items-center justify-center p-4">
            <div class="relative bg-theme-card rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto border border-theme-border"
                 @click.stop>
                <div class="sticky top-0 bg-theme-card border-b border-theme-border p-4 flex items-center justify-between">
                    <h3 class="text-lg font-semibold" x-text="formatAuditType(selectedWorkflow?.audit_type) + ' Details'"></h3>
                    <button @click="selectedWorkflow = null" class="text-theme-muted hover:text-theme-text">&times;</button>
                </div>
                <div class="p-4" x-show="selectedWorkflow">
                    <!-- Progress Summary -->
                    <div class="mb-6">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-theme-muted">Progress</span>
                            <span class="text-sm" x-text="selectedWorkflow?.current_step + '/' + selectedWorkflow?.total_steps + ' steps'"></span>
                        </div>
                        <div class="w-full bg-theme-border rounded-full h-3">
                            <div class="h-3 rounded-full transition-all duration-300"
                                 :class="selectedWorkflow?.status === 'completed' ? 'bg-green-600' : 'bg-theme-accent'"
                                 :style="'width: ' + (selectedWorkflow?.progress_percent || 0) + '%'"></div>
                        </div>
                        <div class="flex items-center justify-between mt-2 text-sm">
                            <span class="px-2 py-1 rounded-full text-xs"
                                  :class="getConfidenceClasses(selectedWorkflow?.confidence)"
                                  x-text="'Confidence: ' + selectedWorkflow?.confidence"></span>
                            <span class="text-theme-muted">
                                <template x-if="selectedWorkflow?.status === 'completed'">
                                    <span x-text="selectedWorkflow?.findings_count + ' findings, '"></span>
                                </template>
                                <span x-text="selectedWorkflow?.files_checked_count + ' files checked'"></span>
                            </span>
                        </div>
                    </div>

                    <!-- Workflow ID -->
                    <div class="mb-4 flex items-center gap-2 text-sm">
                        <span class="text-theme-muted">ID:</span>
                        <code class="bg-theme-bg px-2 py-1 rounded text-xs font-mono" x-text="selectedWorkflow?.id"></code>
                        <button @click="copyWorkflowId()"
                                class="text-theme-muted hover:text-theme-text transition-colors"
                                title="Copy ID to clipboard">
                            <span class="text-sm">📋</span>
                        </button>
                    </div>

                    <!-- Step History -->
                    <div class="mb-6" x-show="selectedWorkflow?.step_history?.length > 0">
                        <h4 class="font-medium mb-3">Step History</h4>
                        <div class="space-y-3">
                            <template x-for="(step, index) in selectedWorkflow?.step_history || []" :key="'step-' + index">
                                <div class="bg-theme-bg rounded-lg p-3 border-l-2"
                                     :class="getStepBorderClass(step.step_number, selectedWorkflow?.current_step)">
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="font-medium text-sm" x-text="'Step ' + step.step_number"></span>
                                        <span class="text-xs px-2 py-0.5 rounded-full"
                                              :class="getConfidenceClasses(step.confidence)"
                                              x-text="step.confidence"></span>
                                    </div>
                                    <p class="text-sm text-theme-muted mb-1" x-text="step.step_content"></p>
                                    <p class="text-xs text-theme-muted" x-text="step.findings"></p>
                                    <div class="flex items-center justify-between mt-2 text-xs text-theme-muted">
                                        <span x-text="step.files_checked_count + ' files checked'"></span>
                                        <span x-text="formatTime(step.timestamp)"></span>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- Issues -->
                    <div x-show="selectedWorkflow?.issues?.length > 0">
                        <h4 class="font-medium mb-3">Issues Found</h4>
                        <div class="space-y-2">
                            <template x-for="(issue, index) in selectedWorkflow?.issues || []" :key="index">
                                <div class="bg-theme-bg rounded-lg p-3 flex items-start gap-3">
                                    <span class="text-xs w-14 py-1 rounded-full font-medium shrink-0 text-center"
                                          :class="getSeverityClasses(issue.severity)"
                                          x-text="issue.severity"></span>
                                    <div class="min-w-0">
                                        <p class="text-sm" x-text="issue.description"></p>
                                        <p class="text-xs text-theme-muted mt-1" x-show="issue.location" x-text="issue.location"></p>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Report Modal -->
    <div x-show="selectedReport" x-cloak
         @keydown.escape.window="selectedReport = null"
         class="fixed inset-0 z-50 overflow-y-auto">
        <div class="fixed inset-0 bg-black/50" @click="selectedReport = null"></div>
        <div class="relative min-h-screen flex items-center justify-center p-4">
            <div class="relative bg-theme-card rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-theme-border"
                 @click.stop>
                <div class="sticky top-0 bg-theme-card border-b border-theme-border p-4 flex items-center justify-between">
                    <h3 class="text-lg font-semibold truncate" x-text="selectedReport?.filename"></h3>
                    <button @click="selectedReport = null" class="text-theme-muted hover:text-theme-text">&times;</button>
                </div>
                <div class="p-4">
                    <div class="prose prose-sm max-w-none"
                         :class="darkMode ? 'prose-invert' : ''"
                         x-html="renderedReport"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div x-show="toast" x-cloak
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0 translate-y-2"
         x-transition:enter-end="opacity-100 translate-y-0"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100 translate-y-0"
         x-transition:leave-end="opacity-0 translate-y-2"
         class="fixed bottom-6 right-6 z-50 bg-theme-card border border-theme-border rounded-lg px-4 py-3 shadow-lg flex items-center gap-2">
        <span class="text-green-500">✓</span>
        <span class="text-sm" x-text="toast"></span>
    </div>

    <!-- Footer -->
    <footer class="border-t border-theme-border mt-8 py-4 text-center text-xs text-theme-muted">
        <span x-text="health?.server_name || 'Optix MCP Server'"></span>
        <span class="mx-2">|</span>
        <span x-text="'v' + (health?.version || '0.0.0')"></span>
        <span class="mx-2">|</span>
        <span>Uptime: <span x-text="health?.uptime_formatted || '-'"></span></span>
    </footer>

    <script>
        function dashboard() {
            return {
                activeTab: 'workflows',
                workflows: [],
                reports: [],
                reportFilter: 'all',
                health: null,
                error: null,
                selectedWorkflow: null,
                selectedReport: null,
                renderedReport: '',
                pollInterval: null,
                projectName: null,
                debugWorkflowId: '',
                debugState: null,
                debugError: null,
                darkMode: localStorage.getItem('optix-theme') !== 'light',
                toast: null,
                toastTimeout: null,

                init() {
                    this.fetchHealth();
                    this.fetchWorkflows();
                    this.fetchReports();
                    this.fetchProject();

                    this.pollInterval = setInterval(() => {
                        this.fetchHealth();
                        this.fetchWorkflows();
                        this.fetchReports();
                        this.fetchProject();
                    }, 5000);
                },

                toggleTheme() {
                    this.darkMode = !this.darkMode;
                    localStorage.setItem('optix-theme', this.darkMode ? 'dark' : 'light');
                    document.documentElement.classList.toggle('dark', this.darkMode);
                },

                showToast(message) {
                    if (this.toastTimeout) clearTimeout(this.toastTimeout);
                    this.toast = message;
                    this.toastTimeout = setTimeout(() => { this.toast = null; }, 2000);
                },

                async fetchHealth() {
                    try {
                        const res = await fetch('/api/health');
                        const data = await res.json();
                        if (data.success) {
                            this.health = data.data;
                        }
                    } catch (e) {
                        this.error = 'Failed to connect to server';
                    }
                },

                async fetchWorkflows() {
                    try {
                        const res = await fetch('/api/workflows');
                        const data = await res.json();
                        if (data.success) {
                            this.workflows = data.data;
                            this.error = null;
                        }
                    } catch (e) {
                        this.error = 'Failed to fetch workflows';
                    }
                },

                async fetchReports() {
                    try {
                        const res = await fetch('/api/reports');
                        const data = await res.json();
                        if (data.success) {
                            this.reports = data.data;
                        }
                    } catch (e) {
                        console.error('Failed to fetch reports:', e);
                    }
                },

                async fetchProject() {
                    try {
                        const res = await fetch('/api/project');
                        const data = await res.json();
                        if (data.success) {
                            this.projectName = data.data.project_name;
                        }
                    } catch (e) {
                        console.error('Failed to fetch project info:', e);
                    }
                },

                async showWorkflowDetail(id) {
                    try {
                        const res = await fetch('/api/workflows/' + id);
                        const data = await res.json();
                        if (data.success) {
                            this.selectedWorkflow = data.data;
                        }
                    } catch (e) {
                        this.error = 'Failed to fetch workflow details';
                    }
                },

                async showReport(filename) {
                    try {
                        const res = await fetch('/api/reports/' + encodeURIComponent(filename));
                        const data = await res.json();
                        if (data.success) {
                            this.selectedReport = data.data;
                            this.renderedReport = marked.parse(data.data.content);
                            this.$nextTick(() => {
                                document.querySelectorAll('.prose pre code').forEach((block) => {
                                    hljs.highlightElement(block);
                                });
                            });
                        }
                    } catch (e) {
                        this.error = 'Failed to fetch report';
                    }
                },

                async fetchDebugState() {
                    if (!this.debugWorkflowId) return;
                    this.debugError = null;
                    this.debugState = null;
                    try {
                        const res = await fetch('/api/debug/' + encodeURIComponent(this.debugWorkflowId));
                        const data = await res.json();
                        if (data.success) {
                            this.debugState = data.data;
                        } else {
                            this.debugError = data.error || 'Failed to fetch debug state';
                        }
                    } catch (e) {
                        this.debugError = 'Failed to fetch debug state';
                    }
                },

                copyDebugState() {
                    if (!this.debugState) return;
                    const text = JSON.stringify(this.debugState, null, 2);
                    navigator.clipboard.writeText(text).then(() => {
                        this.showToast('Debug state copied to clipboard');
                    }).catch(e => {
                        console.error('Failed to copy:', e);
                    });
                },

                copyWorkflowId() {
                    if (!this.selectedWorkflow?.id) return;
                    navigator.clipboard.writeText(this.selectedWorkflow.id).then(() => {
                        this.showToast('Workflow ID copied to clipboard');
                    }).catch(e => {
                        console.error('Failed to copy:', e);
                    });
                },

                get activeWorkflows() {
                    return this.workflows.filter(w => w.status === 'active');
                },

                get completedWorkflows() {
                    return this.workflows.filter(w => w.status === 'completed');
                },

                get filteredReports() {
                    if (this.reportFilter === 'all') return this.reports;
                    return this.reports.filter(r => r.audit_type === this.reportFilter);
                },

                reportCountByType(type) {
                    if (type === 'all') return this.reports.length;
                    return this.reports.filter(r => r.audit_type === type).length;
                },

                formatAuditType(type) {
                    const map = {
                        'security_audit': 'Security Audit',
                        'a11y_audit': 'A11y Audit',
                        'devops_audit': 'DevOps Audit',
                        'principal_audit': 'Principal Audit'
                    };
                    return map[type] || type;
                },

                formatTime(isoString) {
                    if (!isoString) return '-';
                    const date = new Date(isoString);
                    return date.toLocaleString();
                },

                getConfidenceClasses(confidence) {
                    const map = {
                        'exploring': 'bg-gray-600 text-gray-200',
                        'low': 'bg-yellow-600 text-yellow-100',
                        'medium': 'bg-orange-600 text-orange-100',
                        'high': 'bg-green-600 text-green-100',
                        'very_high': 'bg-emerald-600 text-emerald-100',
                        'almost_certain': 'bg-blue-600 text-blue-100',
                        'certain': 'bg-blue-600 text-blue-100'
                    };
                    return map[confidence] || 'bg-gray-600 text-gray-200';
                },

                getSeverityClasses(severity) {
                    const map = {
                        'critical': 'bg-red-600 text-red-100',
                        'high': 'bg-orange-600 text-orange-100',
                        'medium': 'bg-yellow-600 text-yellow-100',
                        'low': 'bg-blue-600 text-blue-100',
                        'info': 'bg-gray-600 text-gray-200'
                    };
                    return map[severity] || 'bg-gray-600 text-gray-200';
                },

                getStepBorderClass(stepNum, currentStep) {
                    if (this.selectedWorkflow?.status === 'completed') {
                        return 'border-green-500';
                    }
                    if (stepNum === currentStep) return 'border-blue-500';
                    if (stepNum < currentStep) return 'border-green-500';
                    return 'border-theme-border';
                }
            };
        }
    </script>
</body>
</html>'''
