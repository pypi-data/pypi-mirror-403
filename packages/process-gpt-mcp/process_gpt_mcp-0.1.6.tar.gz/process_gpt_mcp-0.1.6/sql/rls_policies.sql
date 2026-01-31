-- =============================================================================
-- Work Assistant MCP용 RLS 정책
-- MCP 도구에서 필요한 SELECT 권한만 부여
-- =============================================================================

-- proc_def (프로세스 정의) - SELECT
ALTER TABLE proc_def ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "work-assistant-proc_def_select_policy" ON proc_def;
CREATE POLICY "work-assistant-proc_def_select_policy" ON proc_def 
    FOR SELECT TO authenticated 
    USING (tenant_id = public.tenant_id());

-- form_def (폼 정의) - SELECT
ALTER TABLE form_def ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "work-assistant-form_def_select_policy" ON form_def;
CREATE POLICY "work-assistant-form_def_select_policy" ON form_def 
    FOR SELECT TO authenticated 
    USING (tenant_id = public.tenant_id());

-- bpm_proc_inst (프로세스 인스턴스) - SELECT
ALTER TABLE bpm_proc_inst ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "work-assistant-bpm_proc_inst_select_policy" ON bpm_proc_inst;
CREATE POLICY "work-assistant-bpm_proc_inst_select_policy" ON bpm_proc_inst 
    FOR SELECT TO authenticated 
    USING (tenant_id = public.tenant_id());

-- todolist (할 일 목록) - SELECT
ALTER TABLE todolist ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "work-assistant-todolist_select_policy" ON todolist;
CREATE POLICY "work-assistant-todolist_select_policy" ON todolist 
    FOR SELECT TO authenticated 
    USING (tenant_id = public.tenant_id());

-- configuration (설정/조직도) - SELECT
ALTER TABLE configuration ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "work-assistant-configuration_select_policy" ON configuration;
CREATE POLICY "work-assistant-configuration_select_policy" ON configuration 
    FOR SELECT TO authenticated 
    USING (tenant_id = public.tenant_id());
