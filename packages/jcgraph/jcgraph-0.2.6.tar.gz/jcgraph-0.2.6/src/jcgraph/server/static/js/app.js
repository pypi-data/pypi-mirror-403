function app() {
    const instance = {
        // 状态
        loading: false,
        projects: [],
        currentProject: null,
        currentView: 'projects', // projects, class, method

        // 搜索
        searchQuery: '',
        searchFocused: false,
        searchResults: { classes: [], methods: [], code_refs: [] },
        searchTimeout: null,

        // 类详情
        currentClass: null,
        classMethods: [],

        // 方法详情
        currentMethod: null,
        methodCode: '',
        methodCodeInfo: {},
        activeTab: 'code',

        // 代码查看弹窗
        codeModalOpen: false,
        codeModalLoading: false,
        codeModalMethod: null,
        codeModalCode: '',
        sequenceDepth: 5,
        minImportance: 50, // 最小重要度阈值
        sequenceData: null,
        sequenceLoading: false,
        branchSelections: {}, // 分支选择 {abstract_method_id: selected_impl_id}
        nodeIdCounter: 0, // 节点ID计数器

        // 向上时序图（调用者时序）
        callerSequenceDepth: 10,
        callerSequenceMinImportance: 50,
        callerSequenceData: null,
        callerSequenceLoading: false,

        async init() {
            await this.loadProjects();
        },

        async loadProjects() {
            this.loading = true;
            try {
                const response = await fetch('/api/projects');
                const data = await response.json();
                this.projects = data.projects || [];
            } catch (error) {
                console.error('加载项目失败:', error);
            } finally {
                this.loading = false;
            }
        },

        async selectProject(project) {
            this.currentProject = project;
            this.currentView = 'projects';
            // 可以在这里加载项目的类列表
        },

        // 搜索功能
        debounceSearch() {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => this.search(), 300);
        },

        async search() {
            if (!this.searchQuery || this.searchQuery.length < 2) {
                this.searchResults = { classes: [], methods: [], code_refs: [] };
                this._classNameFormats = null; // 清除缓存
                return;
            }

            try {
                const projectId = this.currentProject?.id || '';
                const response = await fetch(
                    `/api/search?q=${encodeURIComponent(this.searchQuery)}&project_id=${projectId}`
                );
                const data = await response.json();
                this.searchResults = data;
                this._classNameFormats = null; // 清除缓存,下次获取时重新计算
            } catch (error) {
                console.error('搜索失败:', error);
            }
        },

        // 智能显示类名：隐藏相同前缀，突出显示不同部分
        formatClassNameForSearch(classNames) {
            if (!Array.isArray(classNames) || classNames.length === 0) return {};

            // 如果只有一个类名,直接显示最后一段
            if (classNames.length === 1) {
                const parts = classNames[0].split('.');
                return {
                    [classNames[0]]: {
                        prefix: parts.slice(0, -1).join('.'),
                        highlight: parts[parts.length - 1]
                    }
                };
            }

            // 多个类名:找到公共前缀
            const allParts = classNames.map(name => name.split('.'));
            let commonPrefixLength = 0;

            // 找到最短路径的长度
            const minLength = Math.min(...allParts.map(parts => parts.length));

            // 找公共前缀
            for (let i = 0; i < minLength - 1; i++) {  // 至少保留最后一段
                const part = allParts[0][i];
                if (allParts.every(parts => parts[i] === part)) {
                    commonPrefixLength = i + 1;
                } else {
                    break;
                }
            }

            // 为每个类名生成显示格式
            const result = {};
            classNames.forEach((className, index) => {
                const parts = allParts[index];
                const commonPrefix = parts.slice(0, commonPrefixLength).join('.');
                const uniquePart = parts.slice(commonPrefixLength).join('.');

                result[className] = {
                    prefix: commonPrefix,
                    highlight: uniquePart || parts[parts.length - 1]
                };
            });

            return result;
        },

        // 获取格式化后的类名显示
        getFormattedClassName(className) {
            // 如果还没有格式化映射,先计算
            if (!this._classNameFormats || !this._classNameFormats[className]) {
                const allClassNames = this.searchResults.methods.map(m => m.class_name);
                this._classNameFormats = this.formatClassNameForSearch(allClassNames);
            }

            const format = this._classNameFormats[className];
            if (!format) return className;

            if (format.prefix) {
                return `<span class="text-gray-400 text-xs">${format.prefix}.</span><span class="font-medium">${format.highlight}</span>`;
            }
            return `<span class="font-medium">${format.highlight}</span>`;
        },

        async viewClass(cls) {
            this.currentClass = cls;
            this.searchFocused = false;
            this.currentView = 'class';

            // 加载类的方法
            try {
                const response = await fetch(`/api/classes/${encodeURIComponent(cls.id)}/methods`);
                const data = await response.json();
                this.classMethods = data.methods || [];
            } catch (error) {
                console.error('加载方法失败:', error);
            }
        },

        async viewMethod(method) {
            this.currentMethod = method;
            this.currentView = 'method';
            this.activeTab = 'sequence';
            this.searchFocused = false;

            // 默认加载时序图数据
            await this.loadSequence();
        },

        // Tab切换时的处理
        switchTab(tab) {
            this.activeTab = tab;
            // 只在数据不存在时才加载，避免重复加载
            if (tab === 'sequence' && !this.sequenceData) {
                this.loadSequence();
            } else if (tab === 'caller-sequence' && !this.callerSequenceData) {
                this.loadCallerSequence();
            } else if (tab === 'code' && !this.methodCode && this.currentMethod) {
                this.loadMethodCode(this.currentMethod.id);
            }
        },

        async loadSequence() {
            if (!this.currentMethod) {
                console.log('[Sequence] No current method');
                return;
            }

            // 显示 loading 状态
            this.sequenceLoading = true;
            this.sequenceData = null; // 清空旧数据，显示加载中

            // 重置节点ID计数器
            this.nodeIdCounter = 0;

            try {
                const url = `/api/graph/sequence/${encodeURIComponent(this.currentMethod.id)}?depth=${this.sequenceDepth}`;
                console.log('[Sequence] Loading from:', url);
                console.log('[Sequence] Branch selections:', this.branchSelections);

                // 使用POST请求发送分支选择和最小重要度
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        branches: this.branchSelections,
                        min_importance: this.minImportance
                    })
                });

                this.sequenceData = await response.json();
                console.log('[Sequence] Loaded data:', this.sequenceData);
                console.log('[Sequence] Calls count:', this.sequenceData?.calls?.length);
                console.log('[Sequence] Branch points:', this.sequenceData?.branch_points?.length);

                // 等待DOM更新后添加分支选择器事件
                this.$nextTick(() => {
                    this.attachBranchSelectorHandlers();
                });
            } catch (error) {
                console.error('加载时序图失败:', error);
                this.sequenceData = null; // 确保错误时也清空
            } finally {
                this.sequenceLoading = false;
            }
        },

        // 加载调用者时序图（向上时序）
        async loadCallerSequence() {
            if (!this.currentMethod) {
                console.log('[CallerSequence] No current method');
                return;
            }

            this.callerSequenceLoading = true;
            this.callerSequenceData = null;

            try {
                this.callerSequenceData = await window.sequenceLoader.loadUpwardSequence(
                    this.currentMethod.id,
                    {
                        depth: this.callerSequenceDepth,
                        minImportance: this.callerSequenceMinImportance,
                        useCache: false
                    }
                );
                console.log('[CallerSequence] Loaded:', this.callerSequenceData);
            } catch (error) {
                console.error('加载调用者时序图失败:', error);
                this.callerSequenceData = null;
            } finally {
                this.callerSequenceLoading = false;
            }
        },

        // 渲染调用者时序图
        renderCallerSequence(data) {
            if (!data) return '';
            return window.sequenceRenderer.render(data, 'up');
        },

        // 统计调用者数量
        countCallers(data) {
            if (!data) return 0;
            return window.sequenceRenderer.countNodes(data, 'up');
        },

        toggleFoldNode(nodeId) {
            const childrenDiv = document.getElementById(`children-${nodeId}`);
            if (!childrenDiv) {
                console.warn('Cannot find children div for node:', nodeId);
                return;
            }

            const isFolded = childrenDiv.classList.contains('folded');

            if (isFolded) {
                // 展开
                childrenDiv.classList.remove('folded');
                // 更新按钮文本 - 通过父节点找到按钮
                const parentNode = childrenDiv.previousElementSibling;
                if (parentNode) {
                    const foldBtn = parentNode.querySelector('.fold-btn');
                    if (foldBtn) foldBtn.textContent = '[−]';
                }
            } else {
                // 折叠
                childrenDiv.classList.add('folded');
                // 只计算直接子节点数量
                const childCount = childrenDiv.querySelectorAll(':scope > .sequence-node').length;
                // 更新按钮文本
                const parentNode = childrenDiv.previousElementSibling;
                if (parentNode) {
                    const foldBtn = parentNode.querySelector('.fold-btn');
                    if (foldBtn) foldBtn.textContent = `[+${childCount}]`;
                }
            }
        },

        attachBranchSelectorHandlers() {
            // 为所有分支选择器添加change事件
            const selectors = document.querySelectorAll('.branch-selector');
            console.log('[Sequence] Attaching branch selectors to', selectors.length, 'elements');

            selectors.forEach(selector => {
                selector.onchange = (e) => {
                    const abstractMethodId = selector.getAttribute('data-abstract-method-id');
                    const selectedImplId = selector.value;
                    console.log('[Sequence] Branch changed:', abstractMethodId, '->', selectedImplId);

                    // 更新分支选择
                    this.branchSelections[abstractMethodId] = selectedImplId;

                    // 重新加载序列图
                    this.loadSequence();
                };
            });
        },

        countCalls(node) {
            if (!node || !node.calls) return 0;
            let count = node.calls.length;
            for (const call of node.calls) {
                if (call.calls) {
                    count += this.countCalls(call);
                }
            }
            return count;
        },

        renderSequence(node, depth) {
            if (!node || !node.calls) {
                console.log('[Render] No node or no calls at depth', depth, node);
                return '';
            }

            console.log(`[Render] Rendering ${node.calls.length} calls at depth ${depth}`);
            const indent = '  '.repeat(depth);
            let html = '';

            // 按loop_id分组调用
            const loopGroups = new Map();
            const nonLoopCalls = [];

            for (const call of node.calls) {
                if (call.loop_id) {
                    if (!loopGroups.has(call.loop_id)) {
                        loopGroups.set(call.loop_id, []);
                    }
                    loopGroups.get(call.loop_id).push(call);
                } else {
                    nonLoopCalls.push(call);
                }
            }

            // 按branch_id分组调用
            const branchGroups = new Map();
            const processedBranches = new Set();

            for (const call of node.calls) {
                if (call.branch_id && !processedBranches.has(call.branch_id)) {
                    const branchCalls = node.calls.filter(c => c.branch_id === call.branch_id);
                    branchGroups.set(call.branch_id, branchCalls.sort((a, b) => a.branch_order - b.branch_order));
                    processedBranches.add(call.branch_id);
                }
            }

            // 记录已渲染的分支组
            const renderedBranches = new Set();

            // 渲染所有调用（保持原始顺序）
            for (let i = 0; i < node.calls.length; i++) {
                const call = node.calls[i];

                // 如果是分支调用且该分支组未渲染，渲染整个分支组
                if (call.branch_id && !renderedBranches.has(call.branch_id)) {
                    const branchCalls = branchGroups.get(call.branch_id) || [];
                    renderedBranches.add(call.branch_id);

                    const totalIndent = depth * 20;

                    // 开始分支块（用浅色背景和边框标识）
                    html += `<div class="branch-group" style="padding-left: ${totalIndent}px">`;

                    // 按 branch_order 分组
                    const branchesMap = new Map();
                    for (const bc of branchCalls) {
                        if (!branchesMap.has(bc.branch_order)) {
                            branchesMap.set(bc.branch_order, []);
                        }
                        branchesMap.get(bc.branch_order).push(bc);
                    }

                    // 按顺序渲染每个分支
                    const sortedOrders = Array.from(branchesMap.keys()).sort((a, b) => a - b);

                    for (let orderIdx = 0; orderIdx < sortedOrders.length; orderIdx++) {
                        const order = sortedOrders[orderIdx];
                        const callsInBranch = branchesMap.get(order);
                        const firstCall = callsInBranch[0];

                        const branchType = (firstCall.branch_type || 'unknown').toUpperCase();
                        const condition = firstCall.branch_condition || '';

                        // 构建分支标签
                        let branchLabel = '';
                        if (branchType === 'IF' || branchType === 'ELSE-IF') {
                            branchLabel = `${branchType} (${condition})`;
                        } else if (branchType === 'ELSE') {
                            branchLabel = 'ELSE';
                        } else if (branchType === 'CASE') {
                            branchLabel = `CASE ${condition}`;
                        } else if (branchType === 'DEFAULT') {
                            branchLabel = 'DEFAULT';
                        } else {
                            branchLabel = branchType;
                        }

                        // 渲染该分支的所有调用
                        for (const branchCall of callsInBranch) {
                            // 在同一行显示：分支条件 → 方法调用
                            html += this.renderBranchCall(branchCall, depth, branchLabel, orderIdx === 0);
                            // 只在第一个调用显示分支标签，后续调用不重复显示
                            branchLabel = null;
                        }
                    }

                    html += `</div>`;

                    continue;  // 跳过后续处理，因为已经渲染了
                }

                // 如果已经作为分支组的一部分渲染过，跳过
                if (call.branch_id && renderedBranches.has(call.branch_id)) {
                    continue;
                }

                // 普通调用渲染
                html += this.renderSingleCall(call, depth, i, node);
            }

            return html;
        },

        // 渲染分支内的调用（分支条件和调用在同一行）
        renderBranchCall(call, depth, branchLabel, isFirstBranch) {
            let html = '';
            const indent = '  '.repeat(depth);
            const totalIndent = depth * 20;

            if (!call.resolved || call.external || !call.method) {
                // 未解析的调用或外部依赖调用
                const displayText = call.raw || call.target_id || '未知调用';
                const styleClass = call.external ? 'text-blue-600' : 'text-gray-400';
                if (branchLabel) {
                    html += `<div class="branch-call-row" style="padding-left: ${totalIndent}px">
                        ${indent}├─ <span class="branch-condition">${branchLabel}</span> → <span class="${styleClass}">${displayText}</span>
                    </div>`;
                } else {
                    html += `<div class="branch-call-row branch-continuation" style="padding-left: ${totalIndent}px">
                        ${indent}│  <span class="${styleClass}">${displayText}</span>
                    </div>`;
                }
                return html;
            }

            const method = call.method;
            const formattedSignature = this.formatMethodSignature(method);
            const classDisplay = method.class_name ? method.class_name.split('.').pop() : '';
            const escapedMethodId = method.id.replace(/'/g, "\\'");

            // 获取重要度和过滤状态
            const importanceLevel = method.importance_level || 'NORMAL';
            const importanceScore = method.importance_score || 50;
            let importanceClass = 'importance-normal';
            switch (importanceLevel) {
                case 'CRITICAL': importanceClass = 'importance-critical'; break;
                case 'IMPORTANT': importanceClass = 'importance-important'; break;
                case 'NORMAL': importanceClass = 'importance-normal'; break;
                case 'AUXILIARY': importanceClass = 'importance-auxiliary'; break;
            }


            if (branchLabel) {
                // 第一个调用，显示分支条件
                html += `<div class="branch-call-row ${importanceClass}" style="padding-left: ${totalIndent}px">
                    ${indent}├─ <span class="line-number">${call.line}</span>
                    <span class="branch-condition">${branchLabel}</span> →
                    <span class="importance-dot"></span>
                    <span class="cursor-pointer">
                        <span class="method-name hover:underline" onclick="if(!event.target.classList.contains('type-link')) window.app_instance.openCodeModal('${escapedMethodId}')">${formattedSignature.methodName}</span><span class="method-params">(${formattedSignature.params})</span> : <span class="method-return">${formattedSignature.returnType}</span>
                    </span>
                    ${classDisplay ? `<span class="text-xs text-gray-500 ml-2 class-name">${classDisplay}</span>` : ''}
                    <span class="text-xs text-gray-400 ml-2" title="重要度: ${importanceLevel}">(${importanceScore})</span>
                </div>`;
            } else {
                // 后续调用，不显示分支条件
                html += `<div class="branch-call-row branch-continuation ${importanceClass}" style="padding-left: ${totalIndent}px">
                    ${indent}│  <span class="line-number">${call.line}</span>
                    <span class="importance-dot"></span>
                    <span class="cursor-pointer">
                        <span class="method-name hover:underline" onclick="if(!event.target.classList.contains('type-link')) window.app_instance.openCodeModal('${escapedMethodId}')">${formattedSignature.methodName}</span><span class="method-params">(${formattedSignature.params})</span> : <span class="method-return">${formattedSignature.returnType}</span>
                    </span>
                    ${classDisplay ? `<span class="text-xs text-gray-500 ml-2 class-name">${classDisplay}</span>` : ''}
                    <span class="text-xs text-gray-400 ml-2" title="重要度: ${importanceLevel}">(${importanceScore})</span>
                </div>`;
            }

            // 递归渲染子调用
            if (call.calls && call.calls.length > 0) {
                html += `<div class="branch-subcalls">`;
                html += this.renderSequence(call, depth + 1);
                html += `</div>`;
            }

            return html;
        },

        // JDK 内置类型（不需要点击查看字段）
        jdkTypes: new Set(['String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Byte', 'Short', 'Character',
            'List', 'Map', 'Set', 'ArrayList', 'HashMap', 'HashSet', 'LinkedList', 'TreeMap', 'TreeSet',
            'Collection', 'Object', 'Class', 'void', 'int', 'long', 'double', 'float', 'boolean', 'byte', 'short', 'char',
            'LocalDate', 'LocalDateTime', 'LocalTime', 'Date', 'Timestamp', 'BigDecimal', 'BigInteger'
        ]),

        // 标记事件是否已绑定
        typeLinkEventsBound: false,

        // 提取类型字符串中的自定义类型
        extractCustomTypes(typeStr) {
            // 匹配类型标识符（大写开头的驼峰命名）
            const regex = /\b([A-Z][a-zA-Z0-9_]*)\b/g;
            const matches = [];
            let match;
            while ((match = regex.exec(typeStr)) !== null) {
                const typeName = match[1];
                if (!this.jdkTypes.has(typeName)) {
                    matches.push(typeName);
                }
            }
            return [...new Set(matches)]; // 去重
        },

        // 将类型字符串中的自定义类型转换为可点击链接
        renderTypeWithLinks(typeStr, projectId) {
            if (!typeStr) return '';

            const customTypes = this.extractCustomTypes(typeStr);
            let result = typeStr;

            // 替换每个自定义类型为可点击链接
            customTypes.forEach(typeName => {
                const regex = new RegExp(`\\b${typeName}\\b`, 'g');
                result = result.replace(regex,
                    `<a href="#" class="type-link text-blue-600 hover:text-blue-800 hover:underline" data-type="${typeName}" data-project-id="${projectId}">${typeName}</a>`
                );
            });

            return result;
        },

        // 格式化方法签名：使用 params 数据，并为类型添加点击链接
        // 返回结构化的对象，包含方法名和参数/返回类型的 HTML
        formatMethodSignature(method) {
            const projectId = (this.currentProject && this.currentProject.id) || method.project_id;

            // 使用 params 数据（如果存在）
            let paramTypes = '';
            if (method.params && method.params.length > 0) {
                paramTypes = method.params.map(p => {
                    const simpleType = p.type.split('.').pop();
                    return this.renderTypeWithLinks(simpleType, projectId);
                }).join(', ');
            } else if (method.signature) {
                // 降级：从 signature 解析
                const signatureMatch = method.signature.match(/\((.*?)\)/);
                if (signatureMatch) {
                    const paramsStr = signatureMatch[1].trim();
                    if (paramsStr) {
                        const params = paramsStr.split(',').map(p => p.trim());
                        paramTypes = params.map(param => {
                            const parts = param.trim().split(/\s+/);
                            const type = parts[0].split('.').pop();
                            return this.renderTypeWithLinks(type, projectId);
                        }).join(', ');
                    }
                }
            }

            // 处理返回类型
            const returnType = method.return_type ? method.return_type.split('.').pop() : 'void';
            const returnTypeWithLinks = this.renderTypeWithLinks(returnType, projectId);

            return {
                methodName: method.name,
                params: paramTypes,
                returnType: returnTypeWithLinks
            };
        },

        renderSingleCall(call, depth, index, parentNode) {
            let html = '';
            const indent = '  '.repeat(depth);

            if (!call.resolved || call.external || !call.method) {
                // 未解析的调用或外部依赖调用
                const displayText = call.raw || call.target_id || '未知调用';
                const styleClass = call.external ? 'text-blue-600' : 'text-gray-400';
                const loopTag = call.loop_type ? ` <span class="loop-tag">[${call.loop_type.toUpperCase()}]</span>` : '';
                html += `<div class="py-1 ${styleClass}" style="padding-left: ${depth * 20}px">
                    ${indent}├─ <span class="line-number">${call.line}</span> ${displayText}${loopTag}
                </div>`;
                return html;
            }

            const method = call.method;
            const hasSubCalls = call.calls && call.calls.length > 0;
            const methodDisplay = method.name || method.id;
            const classDisplay = method.class_name ? method.class_name.split('.').pop() : '';
            const isBranchPoint = call.is_branch_point || false;

            // 循环标记：检查是否是循环内的第一个调用
            let loopTag = '';
            if (call.loop_type && call.loop_id && parentNode) {
                // 检查是否是该loop_id的第一次出现
                const prevCalls = parentNode.calls.slice(0, index);
                const isFirstInLoop = !prevCalls.some(c => c.loop_id === call.loop_id);
                if (isFirstInLoop) {
                    loopTag = ` <span class="loop-tag" title="循环类型: ${call.loop_type}">[${call.loop_type.toUpperCase()} LOOP]</span>`;
                }
            }

            // 获取重要度级别和样式、过滤状态
            const importanceLevel = method.importance_level || 'NORMAL';
            const importanceScore = method.importance_score || 50;
            let importanceClass = 'importance-normal';

            switch (importanceLevel) {
                case 'CRITICAL':
                    importanceClass = 'importance-critical';
                    break;
                case 'IMPORTANT':
                    importanceClass = 'importance-important';
                    break;
                case 'NORMAL':
                    importanceClass = 'importance-normal';
                    break;
                case 'AUXILIARY':
                    importanceClass = 'importance-auxiliary';
                    break;
            }


            // 生成唯一节点ID
            const nodeId = `node-${this.nodeIdCounter++}`;

            // 折叠按钮(仅当有子调用时显示)
            let foldBtn = '';
            if (hasSubCalls) {
                foldBtn = `<span class="fold-btn" onclick="window.app_instance.toggleFoldNode('${nodeId}')">[−]</span>`;
            }

            // 如果是分支点或接口调用，显示分支选择器
            let branchSelector = '';
            if ((isBranchPoint && call.branch_info) || (call.is_interface_call && call.implementations)) {
                let impls, selectedId, abstractMethodId;

                if (call.branch_info) {
                    // 原有的分支点逻辑
                    const branchInfo = call.branch_info;
                    impls = branchInfo.implementations;
                    selectedId = branchInfo.selected_id;
                    abstractMethodId = branchInfo.abstract_method_id;
                } else if (call.implementations) {
                    // 新增的接口调用逻辑
                    impls = call.implementations;
                    selectedId = impls[0]?.id; // 默认选中第一个
                    abstractMethodId = method.id;
                }

                if (impls && impls.length > 0) {
                    const implCount = impls.length;
                    branchSelector = `
                        <select class="branch-selector ml-2 text-xs border border-gray-300 rounded px-1 py-0.5 bg-yellow-50"
                                data-abstract-method-id="${abstractMethodId}"
                                onclick="event.stopPropagation()">
                            ${impls.map(impl => {
                                const label = impl.branch_label || impl.class_name.split('.').pop();
                                const isSelected = impl.id === selectedId ? 'selected' : '';
                                return `<option value="${impl.id}" ${isSelected}>${label}</option>`;
                            }).join('')}
                            </select>
                            <span class="text-xs text-yellow-600 ml-1">[${implCount}个实现 ▼]</span>
                        `;
                    }
            }

            // 转义 method.id 以避免 HTML 属性中的特殊字符问题
            const escapedMethodId = method.id.replace(/'/g, "\\'");

            // 循环内的调用额外缩进
            const loopIndent = call.loop_id ? 20 : 0;
            const totalIndent = depth * 20 + loopIndent;

            // 格式化方法签名
            const formattedSignature = this.formatMethodSignature(method);

            html += `<div class="sequence-node ${importanceClass} ${call.loop_id ? 'in-loop' : ''}" style="padding-left: ${totalIndent}px">
                ${foldBtn}
                ${indent}├─ <span class="line-number">${call.line}</span>
                <span class="importance-dot"></span>
                <span class="seq-method-call cursor-pointer">
                    <span class="method-name hover:underline" onclick="if(!event.target.classList.contains('type-link')) window.app_instance.openCodeModal('${escapedMethodId}')">${formattedSignature.methodName}</span><span class="method-params">(${formattedSignature.params})</span> : <span class="method-return">${formattedSignature.returnType}</span>
                </span>
                ${classDisplay ? `<span class="text-xs text-gray-500 ml-2 class-name">${classDisplay}</span>` : ''}
                ${loopTag}
                ${branchSelector}
                <span class="text-xs text-gray-400 ml-2" title="重要度: ${importanceLevel}">(${importanceScore})</span>
            </div>`;

            if (hasSubCalls) {
                html += `<div class="sequence-children" id="children-${nodeId}">`;
                html += this.renderSequence(call, depth + 1);
                html += `</div>`;
            }

            return html;
        },

        viewMethodById(methodId) {
            // 通过ID跳转到方法
            fetch(`/api/nodes/${encodeURIComponent(methodId)}`)
                .then(r => r.json())
                .then(method => {
                    if (method.type === 'method') {
                        this.viewMethod(method);
                    }
                })
                .catch(err => console.error('获取方法失败:', err));
        },

        async loadMethodCode(methodId) {
            try {
                const response = await fetch(`/api/methods/${encodeURIComponent(methodId)}/code`);
                const data = await response.json();
                this.methodCode = data.code || '// 代码不可用';
                this.methodCodeInfo = data;
            } catch (error) {
                console.error('加载代码失败:', error);
                this.methodCode = '// 加载失败';
            }
        },

        formatDate(dateStr) {
            if (!dateStr) return '';
            return new Date(dateStr).toLocaleString('zh-CN');
        },

        async openCodeModal(methodId) {
            // 使用原生 DOM 操作
            const modal = document.getElementById('codeModal');
            const loading = document.getElementById('codeModalLoading');
            const content = document.getElementById('codeModalContent');

            // 显示弹窗和加载状态
            modal.style.display = 'flex';
            loading.style.display = 'block';
            content.style.display = 'none';

            try {
                const response = await fetch(`/api/methods/${encodeURIComponent(methodId)}/code`);
                const data = await response.json();

                // 更新弹窗内容
                document.getElementById('codeModalTitle').textContent = data.method_name || methodId;
                document.getElementById('codeModalFilePath').textContent = data.file_path || '';

                const codeElement = document.getElementById('codeModalCode');
                codeElement.textContent = data.code || '// 代码不可用';

                // 应用语法高亮
                if (window.hljs) {
                    hljs.highlightElement(codeElement);
                }

                // 显示行号信息
                if (data.line_start && data.line_end) {
                    const lineInfo = document.getElementById('codeModalLineInfo');
                    document.getElementById('codeModalLineStart').textContent = data.line_start;
                    document.getElementById('codeModalLineEnd').textContent = data.line_end;
                    lineInfo.style.display = 'block';
                } else {
                    document.getElementById('codeModalLineInfo').style.display = 'none';
                }

                // 保存代码到实例变量供复制使用
                this.codeModalCode = data.code || '';
            } catch (error) {
                console.error('加载代码失败:', error);
                document.getElementById('codeModalCode').textContent = '// 加载失败';
                this.codeModalCode = '';
            } finally {
                // 切换到内容显示
                loading.style.display = 'none';
                content.style.display = 'block';
            }
        },

        closeCodeModal() {
            const modal = document.getElementById('codeModal');
            modal.style.display = 'none';
        },

        copyCode() {
            navigator.clipboard.writeText(this.codeModalCode).then(() => {
                alert('代码已复制到剪贴板');
            }).catch(err => {
                console.error('复制失败:', err);
            });
        },

        // 类型解析和字段查看
        async resolveType(typeName, projectId) {
            try {
                const response = await fetch(`/api/types/resolve?type_name=${encodeURIComponent(typeName)}&project_id=${projectId}`);
                if (!response.ok) throw new Error('Failed to resolve type');
                const data = await response.json();
                return data.classes || [];
            } catch (error) {
                console.error('Type resolution failed:', error);
                return [];
            }
        },

        async getClassFields(classId) {
            try {
                const response = await fetch(`/api/classes/${encodeURIComponent(classId)}/fields`);
                if (!response.ok) throw new Error('Failed to get fields');
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Failed to get fields:', error);
                return null;
            }
        },

        async showFieldsModal(typeName, projectId) {
            // 1. 解析类型名到类 ID
            const classes = await this.resolveType(typeName, projectId);

            if (classes.length === 0) {
                alert(`类型 ${typeName} 未在当前项目中找到\n可能来自外部依赖包，暂不支持查看依赖包中的字段`);
                return;
            }

            const classInfo = classes[0]; // 使用第一个匹配的类

            // 2. 获取字段列表
            const fieldsData = await this.getClassFields(classInfo.id);

            if (!fieldsData) {
                alert('获取字段失败');
                return;
            }

            // 3. 显示弹窗
            const modal = document.getElementById('fieldsModal');
            const className = document.getElementById('fieldsClassName');
            const fieldsTable = document.getElementById('fieldsTableBody');

            className.textContent = classInfo.name;
            fieldsTable.innerHTML = '';

            if (fieldsData.fields.length === 0) {
                fieldsTable.innerHTML = '<tr><td colspan="3" class="px-4 py-2 text-center text-gray-500">该类没有字段</td></tr>';
            } else {
                fieldsData.fields.forEach(field => {
                    const row = document.createElement('tr');
                    row.className = 'border-b';

                    const simpleType = field.return_type ? field.return_type.split('.').pop() : '';
                    const typeWithLinks = this.renderTypeWithLinks(simpleType, projectId);

                    row.innerHTML = `
                        <td class="px-4 py-2">${field.name}</td>
                        <td class="px-4 py-2">${typeWithLinks}</td>
                        <td class="px-4 py-2 text-xs text-gray-500">${field.visibility || ''}</td>
                    `;
                    fieldsTable.appendChild(row);
                });
            }

            modal.style.display = 'flex';
        },

        closeFieldsModal() {
            const modal = document.getElementById('fieldsModal');
            modal.style.display = 'none';
        },

        bindTypeLinkEvents() {
            // 防止重复绑定
            if (this.typeLinkEventsBound) {
                return;
            }
            this.typeLinkEventsBound = true;

            // 绑定类型链接点击事件（使用事件委托）
            document.addEventListener('click', async (event) => {
                if (event.target.classList.contains('type-link')) {
                    event.preventDefault();
                    event.stopPropagation();  // 阻止事件冒泡，避免触发方法名点击
                    const typeName = event.target.dataset.type;
                    const projectId = event.target.dataset.projectId;
                    await this.showFieldsModal(typeName, projectId);
                }
            });
        }
    };

    // 设置全局引用，供 onclick 事件使用
    window.app_instance = instance;

    // 绑定类型链接点击事件
    instance.bindTypeLinkEvents();

    return instance;
}
