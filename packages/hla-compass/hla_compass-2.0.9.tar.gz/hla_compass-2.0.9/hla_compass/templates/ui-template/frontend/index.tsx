/**
 * HLA-Compass UI Module Template
 *
 * Lean scaffold: input form + results rendering.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import './styles.css';
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Space,
  Spin,
  Table,
  Typography,
} from '@hla-compass/design-system';

import { devPost } from './api';
import { applyTheme } from './theme';
import Providers from './src/app/Providers';

const { Paragraph, Text } = Typography;

const DEFAULT_THEME_FALLBACKS = {
  primary: '#827DD3',
  primaryHover: '#6c66b4',
  primaryActive: '#565093',
  text: '#171717',
  background: '#ffffff',
  border: '#e5e5e5',
};

const ensureAntDesignCssVariables = () => {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return { fallbackApplied: false };
  }

  const root = document.documentElement;
  const computed = window.getComputedStyle(root);
  const readVar = (name: string) =>
    (root.style.getPropertyValue(name) || computed.getPropertyValue(name) || '').trim();

  const existingPrimary = readVar('--ant-color-primary');
  const fallbackPrimary = existingPrimary || readVar('--color-primary') || DEFAULT_THEME_FALLBACKS.primary;
  const fallbackPrimaryHover =
    readVar('--ant-color-primary-hover') ||
    readVar('--color-primary-hover') ||
    DEFAULT_THEME_FALLBACKS.primaryHover ||
    fallbackPrimary;
  const fallbackPrimaryActive =
    readVar('--ant-color-primary-active') ||
    readVar('--color-primary-active') ||
    DEFAULT_THEME_FALLBACKS.primaryActive ||
    fallbackPrimary;
  const fallbackText = readVar('--ant-color-text') || readVar('--color-text') || DEFAULT_THEME_FALLBACKS.text;
  const fallbackBackground =
    readVar('--ant-color-bg-base') || readVar('--color-background') || DEFAULT_THEME_FALLBACKS.background;
  const fallbackBorder = readVar('--ant-color-border') || readVar('--color-border') || DEFAULT_THEME_FALLBACKS.border;

  const fallbackVars: Record<string, string> = {
    '--ant-color-primary': fallbackPrimary,
    '--ant-color-primary-hover': fallbackPrimaryHover,
    '--ant-color-primary-active': fallbackPrimaryActive,
    '--ant-primary-color': fallbackPrimary,
    '--ant-primary-color-hover': fallbackPrimaryHover,
    '--ant-primary-color-active': fallbackPrimaryActive,
    '--ant-color-text': fallbackText,
    '--ant-color-text-base': fallbackText,
    '--ant-color-bg-base': fallbackBackground,
    '--ant-color-border': fallbackBorder,
  };

  let fallbackApplied = false;

  Object.entries(fallbackVars).forEach(([varName, value]) => {
    if (!readVar(varName) && value) {
      root.style.setProperty(varName, value);
      fallbackApplied = true;
    }
  });

  return { fallbackApplied };
};

interface ModuleProps {
  onExecute?: (params: any) => Promise<any>;
  initialParams?: any;
}

interface ResultRow {
  [key: string]: unknown;
}

const ModuleUI: React.FC<ModuleProps> = ({ onExecute, initialParams }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState<boolean>(false);
  const [results, setResults] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const { fallbackApplied } = ensureAntDesignCssVariables();
    if (fallbackApplied) {
      applyTheme('system');
    }
  }, []);

  const handleSubmit = useCallback(
    async (values: any) => {
      setError(null);
      setResults(null);
      setSummary(null);
      setLoading(true);

      try {
        const params = {
          param1: values.param1,
          param2: values.param2,
        };

        const result = onExecute
          ? await onExecute(params)
          : await devPost('/execute', { input: params });

        if (result?.status === 'success') {
          setResults(result.results ?? null);
          setSummary(result.summary ?? null);
        } else {
          setError(result?.error?.message || result?.message || 'Processing failed');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      } finally {
        setLoading(false);
      }
    },
    [onExecute]
  );

  const handleClear = useCallback(() => {
    form.resetFields();
    setResults(null);
    setSummary(null);
    setError(null);
  }, [form]);

  const tableRows = useMemo(() => {
    const rows = results?.table;
    return Array.isArray(rows) ? (rows as ResultRow[]) : null;
  }, [results]);

  const tableColumns = useMemo(() => {
    if (!tableRows || tableRows.length === 0) {
      return [];
    }

    const keys = Object.keys(tableRows[0]);
    return keys.map((key) => ({
      title: key,
      dataIndex: key,
      key,
      render: (value: unknown) => {
        if (value === null || value === undefined) {
          return <Text type="secondary">-</Text>;
        }
        if (typeof value === 'number') {
          return <Text className="scientific-number font-mono">{value}</Text>;
        }
        if (typeof value === 'object') {
          return (
            <Text className="font-mono text-xs">
              {JSON.stringify(value)}
            </Text>
          );
        }
        return <Text>{String(value)}</Text>;
      },
    }));
  }, [tableRows]);

  return (
    <Providers>
      <div className="module-container max-w-screen-md mx-auto p-5 space-y-5">
        <Card title="Module Inputs">
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Paragraph className="text-gray-600">
              Update these fields to match your manifest inputs.
            </Paragraph>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              initialValues={initialParams}
            >
              <Form.Item
                label="Parameter 1"
                name="param1"
                rules={[{ required: true, message: 'Required' }]}
              >
                <Input placeholder="Required input" disabled={loading} />
              </Form.Item>
              <Form.Item label="Parameter 2" name="param2">
                <Input placeholder="Optional input" disabled={loading} />
              </Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Run
                </Button>
                <Button onClick={handleClear} disabled={loading}>
                  Reset
                </Button>
              </Space>
            </Form>
          </Space>
        </Card>

        {error && (
          <Alert
            message="Execution failed"
            description={error}
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
          />
        )}

        {loading && (
          <div className="text-center py-6">
            <Spin />
          </div>
        )}

        {(summary || results) && (
          <Card title="Results">
            {summary && (
              <Card size="small" title="Summary" className="mb-3">
                <pre className="bg-white p-3 rounded border text-sm font-mono overflow-auto max-h-60">
                  {JSON.stringify(summary, null, 2)}
                </pre>
              </Card>
            )}
            {tableRows ? (
              <Table
                dataSource={tableRows}
                columns={tableColumns}
                rowKey={(record, idx) => (record as any).id ?? idx}
                className="scientific-table"
                pagination={{ pageSize: 10, showSizeChanger: true }}
              />
            ) : results ? (
              <pre className="bg-white p-3 rounded border text-sm font-mono overflow-auto max-h-80">
                {JSON.stringify(results, null, 2)}
              </pre>
            ) : null}
          </Card>
        )}
      </div>
    </Providers>
  );
};

if (typeof window !== 'undefined') {
  (window as any).ModuleUI = ModuleUI;
}

export default ModuleUI;
