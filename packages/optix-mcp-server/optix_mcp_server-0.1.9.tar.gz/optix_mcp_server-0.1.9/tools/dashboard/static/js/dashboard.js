function dashboard() {
    return {
        activeAudit: 'security',
        workflows: [],
        health: null,
        error: null,
        selectedFinding: null,
        pollInterval: null,
        projectName: null,
        searchQuery: '',
        isRunning: false,
        isPaused: false,
        elapsedTime: 0,
        timerInterval: null,
        toast: null,
        toastTimeout: null,
        severityFilter: 'all',
        showFilterDropdown: false,
        showSettingsModal: false,
        selectedAuditType: 'security_audit',
        workflowsByType: {},
        websocket: null,
        websocketUrl: null,
        websocketConnected: false,

        auditTypes: [
            { id: 'security_audit', name: 'Security' },
            { id: 'a11y_audit', name: 'Accessibility' },
            { id: 'devops_audit', name: 'DevOps' },
            { id: 'principal_audit', name: 'Principal' }
        ],

        auditStepDefinitions: {
            'security_audit': [
                { name: 'Reconnaissance', status: 'pending', findings: null },
                { name: 'Auth & Authorization', status: 'pending', findings: null },
                { name: 'Input Validation', status: 'pending', findings: null },
                { name: 'OWASP Top 10', status: 'pending', findings: null },
                { name: 'Dependencies & Config', status: 'pending', findings: null },
                { name: 'Compliance', status: 'pending', findings: null }
            ],
            'a11y_audit': [
                { name: 'Structural Analysis', status: 'pending', findings: null },
                { name: 'ARIA Labels', status: 'pending', findings: null },
                { name: 'Keyboard Navigation', status: 'pending', findings: null },
                { name: 'Focus Management', status: 'pending', findings: null },
                { name: 'Color Contrast', status: 'pending', findings: null },
                { name: 'Semantic HTML', status: 'pending', findings: null }
            ],
            'devops_audit': [
                { name: 'Docker Audit', status: 'pending', findings: null },
                { name: 'CI/CD Pipeline', status: 'pending', findings: null },
                { name: 'Dependency Security', status: 'pending', findings: null },
                { name: 'Cross-Domain Analysis', status: 'pending', findings: null }
            ],
            'principal_audit': [
                { name: 'Complexity Analysis', status: 'pending', findings: null },
                { name: 'DRY Violations', status: 'pending', findings: null },
                { name: 'Coupling Analysis', status: 'pending', findings: null },
                { name: 'Separation of Concerns', status: 'pending', findings: null },
                { name: 'Maintainability', status: 'pending', findings: null }
            ]
        },

        pipelineSteps: [],

        activityLog: [],
        stepHistory: [],

        findings: [],
        severityCounts: { critical: 0, high: 0, medium: 0, low: 0 },
        workflowFiles: [],

        selectedFile: null,

        init() {
            this.initPipelineSteps();
            this.fetchHealth();
            this.fetchWorkflows();
            this.fetchProject();
            this.initWebSocket();

            this.pollInterval = setInterval(() => {
                if (!this.isPaused) {
                    this.fetchHealth();
                    this.fetchWorkflows();
                    this.fetchProject();
                }
            }, 5000);

            this.timerInterval = setInterval(() => {
                this.elapsedTime++;
            }, 1000);

            this.processWorkflowData();

            document.addEventListener('click', (e) => {
                if (!e.target.closest('.filter-dropdown-container')) {
                    this.showFilterDropdown = false;
                }
            });
        },

        async initWebSocket() {
            try {
                const res = await fetch('/api/websocket');
                const data = await res.json();
                if (data.success && data.data.websocket_available) {
                    this.websocketUrl = data.data.websocket_url;
                    this.connectWebSocket();
                }
            } catch (e) {
                console.log('WebSocket not available, using HTTP fallback');
            }
        },

        connectWebSocket() {
            if (!this.websocketUrl) return;

            try {
                this.websocket = new WebSocket(this.websocketUrl);

                this.websocket.onopen = () => {
                    this.websocketConnected = true;
                    console.log('WebSocket connected');
                };

                this.websocket.onclose = () => {
                    this.websocketConnected = false;
                    console.log('WebSocket disconnected');
                    setTimeout(() => this.connectWebSocket(), 5000);
                };

                this.websocket.onerror = (e) => {
                    console.error('WebSocket error:', e);
                    this.websocketConnected = false;
                };

                this.websocket.onmessage = (event) => {
                    this.handleWebSocketMessage(event.data);
                };
            } catch (e) {
                console.error('Failed to connect WebSocket:', e);
            }
        },

        handleWebSocketMessage(data) {
            try {
                const msg = JSON.parse(data);

                if (msg.action === 'audit_stopped') {
                    if (msg.success) {
                        this.showToast(`${this.getAuditLabel(msg.audit_type)} audit stopped`, 'warning');
                        this.fetchWorkflows();
                    } else {
                        this.showToast(msg.message || 'Failed to stop audit', 'error');
                    }
                } else if (msg.action === 'workflow_cancelled') {
                    this.showToast(`Audit cancelled: ${msg.workflow_id.substring(0, 8)}`, 'info');
                    this.fetchWorkflows();
                } else if (msg.action === 'pong') {
                    console.log('WebSocket pong received');
                } else if (msg.action === 'error') {
                    this.showToast(msg.message || 'WebSocket error', 'error');
                }
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        },

        initPipelineSteps() {
            const steps = this.auditStepDefinitions[this.selectedAuditType] || this.auditStepDefinitions['security_audit'];
            this.pipelineSteps = steps.map(s => ({ ...s }));
        },

        showToast(message, type = 'success') {
            if (this.toastTimeout) clearTimeout(this.toastTimeout);
            this.toast = { message, type };
            this.toastTimeout = setTimeout(() => { this.toast = null; }, 3000);
        },

        togglePause() {
            this.isPaused = !this.isPaused;
            if (this.isPaused) {
                this.showToast('Polling paused', 'info');
            } else {
                this.showToast('Polling resumed', 'success');
                this.fetchWorkflows();
            }
        },

        async stopAudit() {
            const activeWorkflow = this.activeWorkflow;
            if (!activeWorkflow) {
                this.showToast('No active audit to stop', 'warning');
                return;
            }

            const auditLabel = this.getAuditLabel(activeWorkflow.audit_type || this.selectedAuditType);
            if (!confirm(`Are you sure you want to stop the ${auditLabel} audit?`)) {
                return;
            }

            const workflowId = activeWorkflow.id;

            if (this.websocketConnected && this.websocket) {
                this.websocket.send(JSON.stringify({
                    action: 'stop_audit',
                    workflow_id: workflowId
                }));
            } else {
                await this.stopAuditViaHttp(workflowId);
            }
        },

        async stopAuditViaHttp(workflowId) {
            try {
                const res = await fetch(`/api/workflows/${workflowId}/stop`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (data.success && data.data.success) {
                    this.showToast(`${this.getAuditLabel(data.data.audit_type)} audit stopped`, 'warning');
                    this.fetchWorkflows();
                } else {
                    this.showToast(data.data?.message || 'Failed to stop audit', 'error');
                }
            } catch (e) {
                this.showToast('Failed to stop audit: ' + e.message, 'error');
            }
        },

        toggleFilterDropdown() {
            this.showFilterDropdown = !this.showFilterDropdown;
        },

        setSeverityFilter(severity) {
            this.severityFilter = severity;
            this.showFilterDropdown = false;
            this.showToast(`Filtering by: ${severity === 'all' ? 'All severities' : severity}`, 'info');
        },

        downloadFindings() {
            if (this.findings.length === 0) {
                this.showToast('No findings to download', 'warning');
                return;
            }

            const data = {
                exported_at: new Date().toISOString(),
                project: this.projectName,
                audit_type: this.selectedAuditType,
                total_findings: this.totalFindings,
                severity_counts: this.severityCounts,
                findings: this.filteredFindings
            };

            const auditLabel = this.selectedAuditType.replace('_audit', '');
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `optix-${auditLabel}-findings-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showToast(`Downloaded ${this.filteredFindings.length} findings`, 'success');
        },

        openSettings() {
            this.showSettingsModal = true;
        },

        closeSettings() {
            this.showSettingsModal = false;
        },

        selectAuditType(auditId) {
            this.selectedAuditType = auditId;
            this.selectedFile = null;
            this.initPipelineSteps();
            this.processWorkflowData();
            this.showToast(`Switched to ${this.getAuditLabel(auditId)} audit`, 'info');
        },

        getAuditLabel(auditId) {
            const audit = this.auditTypes.find(a => a.id === auditId);
            return audit ? audit.name : 'Unknown';
        },

        getAuditStatus(auditId) {
            const typeWorkflows = this.workflowsByType[auditId] || [];
            if (typeWorkflows.length === 0) return 'empty';
            const hasActive = typeWorkflows.some(w => w.status === 'active');
            if (hasActive) return 'running';
            const latestCompleted = typeWorkflows.some(w => w.status === 'completed');
            if (latestCompleted) return 'completed';
            return 'idle';
        },

        getAuditStatusLabel(auditId) {
            const status = this.getAuditStatus(auditId);
            const labels = {
                'empty': '',
                'running': 'ACTIVE',
                'completed': 'DONE',
                'idle': 'IDLE'
            };
            return labels[status] || '';
        },

        getAuditFindingsCount(auditId) {
            const typeWorkflows = this.workflowsByType[auditId] || [];
            return typeWorkflows.reduce((sum, w) => sum + (w.findings_count || 0), 0);
        },

        hasWorkflowsForType(auditId) {
            return (this.workflowsByType[auditId] || []).length > 0;
        },

        getAuditCommand() {
            const commands = {
                'security_audit': 'claude "run security audit on this codebase"',
                'a11y_audit': 'claude "run accessibility audit on this codebase"',
                'devops_audit': 'claude "run devops audit on this codebase"',
                'principal_audit': 'claude "run principal engineer audit on this codebase"'
            };
            return commands[this.selectedAuditType] || 'claude "run audit"';
        },

        copyAuditCommand() {
            const cmd = this.getAuditCommand();
            navigator.clipboard.writeText(cmd).then(() => {
                this.showToast('Command copied to clipboard!', 'success');
            }).catch(() => {
                this.showToast('Failed to copy', 'error');
            });
        },

        toggleFolder(item) {
            item.expanded = !item.expanded;
        },

        async processWorkflowData() {
            this.workflowsByType = {};
            for (const audit of this.auditTypes) {
                this.workflowsByType[audit.id] = [];
            }

            for (const workflow of this.workflows) {
                const auditType = (workflow.audit_type || 'security_audit').toLowerCase();
                if (!this.workflowsByType[auditType]) {
                    this.workflowsByType[auditType] = [];
                }
                this.workflowsByType[auditType].push(workflow);
            }

            const selectedWorkflows = this.workflowsByType[this.selectedAuditType] || [];

            const counts = { critical: 0, high: 0, medium: 0, low: 0 };
            const allFindings = [];
            const allFiles = new Set();
            const allStepHistory = [];

            for (const workflow of selectedWorkflows) {
                const needsDetail = workflow.findings_count > 0 || workflow.files_checked_count > 0 || workflow.status === 'active';

                if (needsDetail) {
                    const detail = await this.fetchWorkflowDetail(workflow.id);
                    if (detail) {
                        if (detail.files_checked) {
                            detail.files_checked.forEach(f => allFiles.add(f));
                        }
                        if (detail.step_history) {
                            allStepHistory.push(...detail.step_history);
                        }
                        if (detail.issues) {
                            detail.issues.forEach(issue => {
                                const severity = (issue.severity || 'medium').toLowerCase();
                                if (counts[severity] !== undefined) {
                                    counts[severity]++;
                                }
                                allFindings.push({
                                    ...issue,
                                    workflow_id: workflow.id,
                                    audit_type: workflow.audit_type
                                });
                            });
                        }
                    }
                } else if (workflow.issues) {
                    workflow.issues.forEach(issue => {
                        const severity = (issue.severity || 'medium').toLowerCase();
                        if (counts[severity] !== undefined) {
                            counts[severity]++;
                        }
                        allFindings.push({
                            ...issue,
                            workflow_id: workflow.id,
                            audit_type: workflow.audit_type
                        });
                    });
                }
            }

            this.severityCounts = counts;
            this.findings = allFindings.slice(0, 50);
            this.workflowFiles = Array.from(allFiles);
            this.stepHistory = allStepHistory;

            const activeWorkflow = selectedWorkflows.find(w => w.status === 'active');
            const latestWorkflow = selectedWorkflows[0];
            this.isRunning = !!activeWorkflow;

            if (activeWorkflow) {
                this.updatePipelineFromWorkflow(activeWorkflow);
            } else if (latestWorkflow && latestWorkflow.status === 'completed') {
                this.updatePipelineFromWorkflow(latestWorkflow, true);
            } else {
                this.resetPipeline();
            }

            this.activityLog = this.generateActivityLog();
        },

        resetPipeline() {
            this.initPipelineSteps();
        },

        generateActivityLog() {
            const log = [];

            for (const step of this.stepHistory) {
                log.push({
                    type: 'step',
                    message: `Step ${step.step_number}: ${step.step_content || 'Started'}`,
                    timestamp: step.timestamp
                });

                if (step.files_checked_count > 0) {
                    log.push({
                        type: 'file',
                        message: `Analyzing ${step.files_checked_count} files...`,
                        timestamp: step.timestamp
                    });
                }

                if (step.findings) {
                    log.push({
                        type: 'finding',
                        message: step.findings,
                        severity: step.confidence === 'high' ? 'high' : 'medium',
                        timestamp: step.timestamp
                    });
                }

                if (step.status === 'completed') {
                    log.push({
                        type: 'complete',
                        message: `Step ${step.step_number} completed`,
                        timestamp: step.timestamp
                    });
                }
            }

            for (const finding of this.findings.slice(-5)) {
                const existingFinding = log.find(l =>
                    l.type === 'finding' && l.message === finding.description
                );
                if (!existingFinding) {
                    log.push({
                        type: 'finding',
                        message: (finding.description || 'Issue found').substring(0, 60),
                        severity: (finding.severity || 'medium').toLowerCase(),
                        timestamp: finding.detected_at
                    });
                }
            }

            log.sort((a, b) => {
                if (!a.timestamp && !b.timestamp) return 0;
                if (!a.timestamp) return 1;
                if (!b.timestamp) return -1;
                return new Date(a.timestamp) - new Date(b.timestamp);
            });

            return log.slice(-10);
        },

        updatePipelineFromWorkflow(workflow, isCompleted = false) {
            const currentStep = workflow.current_step || 1;
            const totalSteps = workflow.total_steps || 6;

            this.pipelineSteps = this.pipelineSteps.map((step, index) => {
                const stepNum = index + 1;
                let status = 'pending';

                if (isCompleted || workflow.status === 'completed') {
                    status = 'completed';
                } else if (stepNum < currentStep) {
                    status = 'completed';
                } else if (stepNum === currentStep) {
                    status = 'active';
                }

                return { ...step, status };
            });
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
                    this.processWorkflowData();
                }
            } catch (e) {
                this.error = 'Failed to fetch workflows';
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

        async fetchWorkflowDetail(id) {
            try {
                const res = await fetch('/api/workflows/' + id);
                const data = await res.json();
                if (data.success) {
                    return data.data;
                }
            } catch (e) {
                this.error = 'Failed to fetch workflow details';
            }
            return null;
        },

        showFindingDetail(finding) {
            this.selectedFinding = {
                ...finding
            };
        },

        closeFindingDetail() {
            this.selectedFinding = null;
        },

        minimizeFinding() {
            this.showToast('Finding minimized to tray', 'info');
            this.selectedFinding = null;
        },

        hideFinding() {
            if (confirm('Hide this finding from the list?')) {
                this.showToast('Finding hidden', 'info');
                this.selectedFinding = null;
            }
        },

        copyRemediation() {
            if (!this.selectedFinding?.remediation) return;
            navigator.clipboard.writeText(this.selectedFinding.remediation).then(() => {
                this.showToast('Remediation copied to clipboard!', 'success');
            }).catch(() => {
                this.showToast('Failed to copy', 'error');
            });
        },

        selectFile(file) {
            this.selectedFile = file;
        },

        get totalFindings() {
            return this.severityCounts.critical + this.severityCounts.high +
                   this.severityCounts.medium + this.severityCounts.low;
        },

        get filteredFindings() {
            let filtered = this.findings;

            if (this.severityFilter !== 'all') {
                filtered = filtered.filter(f =>
                    (f.severity || 'medium').toLowerCase() === this.severityFilter.toLowerCase()
                );
            }

            if (this.searchQuery.trim()) {
                const query = this.searchQuery.toLowerCase();
                filtered = filtered.filter(f =>
                    (f.description || '').toLowerCase().includes(query) ||
                    (f.location || '').toLowerCase().includes(query) ||
                    (f.severity || '').toLowerCase().includes(query)
                );
            }

            return filtered;
        },

        get filesChecked() {
            return this.workflowFiles.length || this.workflows.reduce((sum, w) => sum + (w.files_checked_count || 0), 0);
        },

        get confidencePercent() {
            const activeWorkflow = this.workflows.find(w => w.status === 'active');
            if (activeWorkflow) {
                return activeWorkflow.progress_percent || 0;
            }
            const latestWorkflow = this.workflows[0];
            if (latestWorkflow && latestWorkflow.status === 'completed') {
                return 100;
            }
            return 0;
        },

        get isCompleted() {
            const latestWorkflow = this.workflows[0];
            return latestWorkflow && latestWorkflow.status === 'completed' && !this.isRunning;
        },

        get latestWorkflow() {
            const selected = this.workflowsByType[this.selectedAuditType] || [];
            return selected[0];
        },

        get confidenceLabel() {
            if (this.isCompleted) return 'COMPLETE';
            const pct = this.confidencePercent;
            if (pct >= 80) return 'HIGH';
            if (pct >= 50) return 'MEDIUM';
            return 'LOW';
        },

        get currentStepIndex() {
            return this.pipelineSteps.findIndex(s => s.status === 'active');
        },

        get activeWorkflow() {
            const selected = this.workflowsByType[this.selectedAuditType] || [];
            return selected.find(w => w.status === 'active');
        },

        get currentAuditType() {
            return this.selectedAuditType;
        },

        get currentAuditLabel() {
            return this.getAuditLabel(this.selectedAuditType);
        },

        get selectedWorkflows() {
            return this.workflowsByType[this.selectedAuditType] || [];
        },

        get analyzedFiles() {
            const fileMap = new Map();

            this.workflowFiles.forEach(filePath => {
                if (!fileMap.has(filePath)) {
                    const name = filePath.split('/').pop();
                    fileMap.set(filePath, {
                        path: filePath,
                        name: name,
                        findingsCount: 0,
                        badgeType: null
                    });
                }
            });

            this.findings.forEach(finding => {
                const location = finding.location;
                if (location && fileMap.has(location)) {
                    const file = fileMap.get(location);
                    file.findingsCount++;
                    const severity = (finding.severity || 'low').toLowerCase();
                    if (severity === 'critical' || (severity === 'high' && file.badgeType !== 'critical')) {
                        file.badgeType = severity;
                    } else if (severity === 'medium' && !['critical', 'high'].includes(file.badgeType)) {
                        file.badgeType = severity;
                    }
                } else if (location) {
                    const name = location.split('/').pop();
                    const severity = (finding.severity || 'low').toLowerCase();
                    fileMap.set(location, {
                        path: location,
                        name: name,
                        findingsCount: 1,
                        badgeType: severity
                    });
                }
            });

            return Array.from(fileMap.values()).sort((a, b) => {
                if (b.findingsCount !== a.findingsCount) {
                    return b.findingsCount - a.findingsCount;
                }
                return a.name.localeCompare(b.name);
            });
        },

        get fileTree() {
            const severityPriority = { critical: 4, high: 3, medium: 2, low: 1, null: 0 };
            const root = { name: '', type: 'folder', children: {}, findingsCount: 0, highestSeverity: null, expanded: true };

            const findingsByFile = new Map();
            this.findings.forEach(finding => {
                const loc = finding.location;
                if (!loc) return;
                if (!findingsByFile.has(loc)) {
                    findingsByFile.set(loc, { count: 0, highestSeverity: null });
                }
                const data = findingsByFile.get(loc);
                data.count++;
                const sev = (finding.severity || 'low').toLowerCase();
                if (severityPriority[sev] > severityPriority[data.highestSeverity]) {
                    data.highestSeverity = sev;
                }
            });

            findingsByFile.forEach((fileData, filePath) => {
                const parts = filePath.split('/').filter(p => p);
                let current = root;

                parts.forEach((part, index) => {
                    const isFile = index === parts.length - 1;
                    if (!current.children[part]) {
                        current.children[part] = {
                            name: part,
                            type: isFile ? 'file' : 'folder',
                            path: parts.slice(0, index + 1).join('/'),
                            children: isFile ? null : {},
                            findingsCount: 0,
                            highestSeverity: null,
                            expanded: index < 2
                        };
                    }
                    current = current.children[part];
                });

                current.findingsCount = fileData.count;
                current.highestSeverity = fileData.highestSeverity;
            });

            const aggregateFolder = (node) => {
                if (node.type === 'file' || !node.children) return;

                Object.values(node.children).forEach(child => {
                    aggregateFolder(child);
                    node.findingsCount += child.findingsCount;
                    if (severityPriority[child.highestSeverity] > severityPriority[node.highestSeverity]) {
                        node.highestSeverity = child.highestSeverity;
                    }
                });
            };

            aggregateFolder(root);

            const toArray = (node) => {
                if (!node.children) return [];
                return Object.values(node.children)
                    .filter(child => child.findingsCount > 0)
                    .map(child => ({
                        ...child,
                        children: child.type === 'folder' ? toArray(child) : null
                    }))
                    .sort((a, b) => {
                        if (a.type !== b.type) return a.type === 'folder' ? -1 : 1;
                        return a.name.localeCompare(b.name);
                    });
            };

            return toArray(root);
        },

        toggleTreeItem(item) {
            item.expanded = !item.expanded;
        },

        get auditId() {
            const workflow = this.activeWorkflow || this.latestWorkflow;
            if (workflow) {
                return '#' + workflow.id.substring(0, 4).toUpperCase();
            }
            return '--';
        },

        formatElapsedTime() {
            void this.elapsedTime;
            const workflow = this.activeWorkflow || this.latestWorkflow;
            if (workflow && workflow.created_at) {
                const start = new Date(workflow.created_at);
                const end = workflow.updated_at ? new Date(workflow.updated_at) : new Date();
                const now = this.isRunning ? new Date() : end;
                const diff = Math.floor((now - start) / 1000);
                const mins = Math.floor(diff / 60);
                const secs = diff % 60;
                return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            }
            return '--:--';
        },

        formatTimeAgo(isoString) {
            if (!isoString) return 'Just now';
            const date = new Date(isoString);
            const now = new Date();
            const diff = Math.floor((now - date) / 1000);

            if (diff < 60) return 'Just now';
            if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
            if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
            return Math.floor(diff / 86400) + 'd ago';
        },

        getStepIndicatorClass(step) {
            return {
                'step-indicator': true,
                'completed': step.status === 'completed',
                'active': step.status === 'active',
                'pending': step.status === 'pending'
            };
        },

        getStepIndicatorContent(step, index) {
            if (step.status === 'completed') return '✓';
            return (index + 1).toString().padStart(2, '0');
        },

        getStepStatusText(step) {
            if (step.status === 'completed') {
                if (step.findings) {
                    return step.findings + ' findings found';
                }
                return 'Completed';
            }
            if (step.status === 'active') {
                return 'Scanning...';
            }
            return 'Pending';
        },

        getSeverityClass(severity) {
            return (severity || 'medium').toLowerCase();
        },

        getSegmentStyle(severity) {
            const total = this.totalFindings || 0;
            if (total === 0) return { dasharray: '0 283', dashoffset: 0 };

            const r = 45;
            const circumference = 2 * Math.PI * r;

            const order = ['critical', 'high', 'medium', 'low'];
            const counts = {
                critical: this.severityCounts.critical,
                high: this.severityCounts.high,
                medium: this.severityCounts.medium,
                low: this.severityCounts.low
            };

            let offset = 0;
            for (const sev of order) {
                if (sev === severity) break;
                offset += (counts[sev] / total) * circumference;
            }

            const segmentLength = (counts[severity] / total) * circumference;

            return {
                dasharray: `${segmentLength} ${circumference}`,
                dashoffset: -offset
            };
        }
    };
}
