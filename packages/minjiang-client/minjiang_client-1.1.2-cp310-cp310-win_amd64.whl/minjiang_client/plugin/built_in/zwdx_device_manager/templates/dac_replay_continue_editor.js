(function () {
    'use strict';

    class DacReplayContinueEditor {
        /**
         * 从wrapper的data属性中获取通道列表
         * @param {HTMLElement} wrapper - 编辑器包装元素
         * @returns {string[]} 通道列表
         */
        static getChannelsFromWrapper(wrapper) {
            // 优先从 data-channels 属性获取（JSON数组字符串）
            if (wrapper.dataset.channels) {
                try {
                    const channels = JSON.parse(wrapper.dataset.channels);
                    if (Array.isArray(channels) && channels.length > 0) {
                        return channels;
                    }
                } catch (err) {
                    console.warn('Failed to parse channels from data-channels:', err);
                }
            }
            
            // 如果没有提供通道列表，尝试从映射值中提取所有键
            let mapping = {};
            try {
                mapping = JSON.parse(wrapper.dataset.dacReplayContinue || '{}');
            } catch (err) {
                // ignore
            }
            
            // 从映射值中提取所有键作为通道列表
            if (mapping && typeof mapping === 'object') {
                const keys = Object.keys(mapping);
                if (keys.length > 0) {
                    return keys.sort();
                }
            }
            
            // 如果都没有，返回空数组（不应该发生，但作为后备）
            return [];
        }

        static getDefaultMap(channels) {
            const blank = {};
            if (Array.isArray(channels) && channels.length > 0) {
                channels.forEach((key) => {
                    blank[key] = false;
                });
            }
            return blank;
        }

        static normalizeMapping(mapping, channels) {
            const normalized = {};
            if (Array.isArray(channels) && channels.length > 0) {
                channels.forEach((key) => {
                    if (mapping && typeof mapping[key] === 'boolean') {
                        normalized[key] = mapping[key];
                    } else {
                        normalized[key] = false;
                    }
                });
            } else if (mapping && typeof mapping === 'object') {
                // 如果没有提供通道列表，使用映射值中的所有键
                Object.keys(mapping).forEach((key) => {
                    if (typeof mapping[key] === 'boolean') {
                        normalized[key] = mapping[key];
                    } else {
                        normalized[key] = false;
                    }
                });
            }
            return normalized;
        }

        static initEditors(root = document) {
            const wrappers = root.querySelectorAll('.dac-replay-continue-editor');
            wrappers.forEach((wrapper) => {
                if (wrapper.dataset.dacReplayContinueReady === 'true') {
                    return;
                }
                DacReplayContinueEditor.mountEditor(wrapper);
            });
        }

        static mountEditor(wrapper) {
            const hiddenId = wrapper.dataset.targetInput;
            const hiddenInput = document.getElementById(hiddenId);
            if (!hiddenInput) {
                return;
            }
            
            // 获取通道列表
            const channels = DacReplayContinueEditor.getChannelsFromWrapper(wrapper);
            
            if (channels.length === 0) {
                console.warn('No channels found for dac_replay_continue editor');
                wrapper.innerHTML = '<div style="color: #f87171; padding: 10px;">未找到通道列表，请检查配置</div>';
                return;
            }
            
            let mapping = {};
            try {
                mapping = JSON.parse(wrapper.dataset.dacReplayContinue || hiddenInput.value || '{}');
            } catch (err) {
                mapping = {};
            }
            const normalized = DacReplayContinueEditor.normalizeMapping(mapping, channels);

            const table = document.createElement('table');
            table.className = 'dac-replay-continue-table';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>硬件通道</th>
                        <th>启用</th>
                    </tr>
                </thead>
            `;
            const tbody = document.createElement('tbody');

            const updateHiddenValue = () => {
                const serialized = JSON.stringify(normalized);
                hiddenInput.value = serialized;
            };

            channels.forEach((hardwareKey) => {
                const currentValue = normalized[hardwareKey];

                const row = document.createElement('tr');
                row.className = 'dac-replay-continue-row';

                const hardwareCell = document.createElement('td');
                hardwareCell.className = 'dac-replay-continue-hw';
                hardwareCell.textContent = hardwareKey;
                row.appendChild(hardwareCell);

                const switchCell = document.createElement('td');
                const switchInput = document.createElement('input');
                switchInput.type = 'checkbox';
                switchInput.className = 'dac-replay-continue-switch';
                switchInput.checked = currentValue === true;
                switchCell.appendChild(switchInput);
                row.appendChild(switchCell);

                const handleChange = () => {
                    normalized[hardwareKey] = switchInput.checked;
                    updateHiddenValue();
                };

                switchInput.addEventListener('change', handleChange);

                tbody.appendChild(row);
            });

            table.appendChild(tbody);

            const tableWrapper = document.createElement('div');
            tableWrapper.className = 'dac-replay-continue-table-wrapper';
            tableWrapper.appendChild(table);

            wrapper.insertBefore(tableWrapper, hiddenInput);
            wrapper.dataset.dacReplayContinueReady = 'true';
            updateHiddenValue();
        }
    }

    window.DacReplayContinueEditor = DacReplayContinueEditor;
})();

