<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" 
  xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" 
  xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" 
  xmlns:math="http://www.w3.org/1998/Math/MathML" 
  xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" 
  xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" 
  xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" 
  xmlns:ooo="http://openoffice.org/2004/office" 
  xmlns:ooow="http://openoffice.org/2004/writer" 
  xmlns:oooc="http://openoffice.org/2004/calc" 
  xmlns:dom="http://www.w3.org/2001/xml-events" 
  xmlns:xforms="http://www.w3.org/2002/xforms" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:rpt="http://openoffice.org/2005/report" 
  xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" 
  xmlns:xhtml="http://www.w3.org/1999/xhtml" 
  xmlns:grddl="http://www.w3.org/2003/g/data-view#" 
  xmlns:officeooo="http://openoffice.org/2009/office" 
  xmlns:tableooo="http://openoffice.org/2009/table" 
  xmlns:drawooo="http://openoffice.org/2010/draw" 
  xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0" 
  xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" 
  xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0" 
  xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" 
  xmlns:css3t="http://www.w3.org/TR/css3-text/"
  xmlns="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="#all">
    
<xsl:output method="xml" encoding="UTF-8" indent="no"/>
    
<xsl:template match="*:cit[not(child::*:sp) and not(@type='linguistic')]">
    <cit>
        <xsl:copy-of select="@*"/>
        <xsl:choose>
            <xsl:when test="child::*[starts-with(@text:style-name,'TEI_verse')]">
                <quote><xsl:apply-templates/></quote>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="child::*">
                    <xsl:choose>
                        <xsl:when test="starts-with(@text:style-name,'TEI_quote') or starts-with(@text:style-name,'TEI_bibl') or (local-name()='p' and child::draw:frame)">
                            <xsl:apply-templates select="."/>
                        </xsl:when>
                        <xsl:otherwise>
                            <quote>
                                <xsl:apply-templates select="."/>
                            </quote>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </cit>
</xsl:template>
    
<xsl:template match="*:cit[child::*:sp]">
    <cit>
        <xsl:copy-of select="@*"/>
        <quote>
            <xsl:apply-templates/>
        </quote>
    </cit>
</xsl:template>
    
<xsl:template match="*:sp[parent::*:cit]">
    <xsl:choose>
        <!-- last child = bibl (move to quote/bibl for validity) -->
        <xsl:when test="child::*[last()]/@text:style-name='TEI_bibl_reference'">
            <sp>
                <xsl:copy-of select="@*"/> 
                <xsl:apply-templates select="child::* except(*[@text:style-name='TEI_bibl_reference'])"/>
             </sp>  
             <xsl:apply-templates select="child::*[last() and @text:style-name='TEI_bibl_reference']"/>
        </xsl:when>
        <xsl:otherwise>
            <sp>
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates/>
            </sp>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_quote')][ancestor::*:cit]">
    <xsl:choose>
        <xsl:when test="@text:style-name='TEI_quote_nested'">
            <cit>
                <xsl:call-template name="quote"/>
            </cit>
        </xsl:when>
        <xsl:otherwise><xsl:call-template name="quote"/></xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_quote')][not(ancestor::*:cit)]">
    <cit>
        <xsl:call-template name="quote"/>
    </cit>
</xsl:template>
    
<xsl:template name="quote">
    <xsl:variable name="quoteType" select="@text:style-name"/>
    <quote>
        <xsl:copy-of select="@rendition|@xml:lang"/>
        <xsl:choose>
                <xsl:when test="$quoteType='TEI_quote2'"><xsl:attribute name="type">quotation2</xsl:attribute></xsl:when>
                <xsl:when test="starts-with($quoteType,'TEI_quote:trl')"><xsl:attribute name="type">trl</xsl:attribute></xsl:when>
                <xsl:otherwise/>
        </xsl:choose>
        <xsl:apply-templates/>
     </quote>
    <xsl:if test="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference'] and not(ancestor::*:cit)">
        <xsl:apply-templates select="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference']" mode="preserve"/>
    </xsl:if>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_bibl_reference'][not(ancestor::div[@type='bibliography'])]">
    <xsl:choose>
        <xsl:when test="ancestor::*:note">
            <p><bibl><xsl:apply-templates/></bibl></p>
        </xsl:when>
        <xsl:when test="ancestor::*:cit and preceding-sibling::text:p[1][@text:style-name='TEI_verse']"></xsl:when>
        <xsl:when test="ancestor::*:cit">
            <bibl><xsl:copy-of select="@rendition"/><xsl:apply-templates/></bibl>
        </xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_quote'] or preceding-sibling::text:p[1][@text:style-name='TEI_quote2']"></xsl:when>
        <xsl:when test="preceding-sibling::text:p[1][@text:style-name='TEI_epigraph']"></xsl:when>
        <xsl:otherwise>
<!--            <xsl:comment><xsl:value-of select="preceding-sibling::*[1]/@text:style-name"/></xsl:comment>-->
            <bibl>
                <xsl:copy-of select="@rendition"/>
                <xsl:apply-templates/>
            </bibl>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_bibl_reference']" mode="preserve">
<!--    <xsl:comment>mode preserve</xsl:comment>-->
    <bibl><xsl:copy-of select="@rendition"/><xsl:apply-templates/></bibl>
</xsl:template>

<xsl:template match="text:span[@text:style-name='TEI_quote-inline']">
    <cit><quote><xsl:copy-of select="@xml:lang"/><xsl:apply-templates/></quote></cit>
</xsl:template>
    
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_epigraph')]">
    <epigraph>
        <cit>
            <quote>
                <xsl:copy-of select="@rendition"/>
                <xsl:apply-templates/>
            </quote>
            <xsl:if test="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference']">
                <xsl:apply-templates select="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference']" mode="preserve"/>
            </xsl:if>
        </cit>
    </epigraph>
</xsl:template>
    
<xsl:template match="text:p[@text:style-name='TEI_verse']">
    <lg>
        <xsl:copy-of select="@rendition|@xml:lang"/>
        <xsl:for-each-group select="node()" group-ending-with="text:line-break">
            <l>
            <xsl:variable name="lineNum" select="."/>
                <xsl:if test="$lineNum/local-name()='span' and $lineNum/@text:style-name='TEI_versenumber-inline'">
                    <xsl:attribute name="n">
                        <xsl:analyze-string select="." regex="(\d+)">
                            <xsl:matching-substring><xsl:value-of select="."/></xsl:matching-substring>
                            <xsl:non-matching-substring></xsl:non-matching-substring>
                        </xsl:analyze-string>
                    </xsl:attribute>
                </xsl:if>
                <xsl:apply-templates select="current-group()"/>
            </l>
        </xsl:for-each-group>
    </lg>
    <xsl:if test="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference']">
        <xsl:apply-templates select="following-sibling::text:p[1][@text:style-name='TEI_bibl_reference']" mode="preserve"/>
    </xsl:if>
</xsl:template>
    
<xsl:template match="text:span[@text:style-name='TEI_versenumber-inline']">
    <num><xsl:apply-templates/></num>
</xsl:template>
    
<xsl:template match="text:tab">
    <xsl:choose>
        <xsl:when test="parent::text:p[@text:style-name='TEI_verse']">
            <caesura/>
        </xsl:when>
        <xsl:otherwise/>
    </xsl:choose>
</xsl:template>
    
<!-- ## entretien ## -->
<xsl:template match="text:p[@text:style-name='TEI_question']|text:p[@text:style-name='TEI_answer']">
    <p>
        <xsl:copy-of select="@rendition"/>
        <xsl:apply-templates/>
    </p>
</xsl:template>

<xsl:template match="text:p[@text:style-name='TEI_speaker']">
    <speaker><xsl:copy-of select="@rendition"/><xsl:apply-templates select="node()[not(local-name()='span' and @text:style-name='TEI_didascaly-inline')]"/></speaker>
    <xsl:apply-templates select="child::text:span[starts-with(@text:style-name,'TEI_didascaly-inline')]"/>
</xsl:template>
    
<xsl:template match="text:span[@text:style-name='TEI_speaker-inline']">
    <name type="speaker"><xsl:apply-templates/></name>
</xsl:template>
    
<!-- ## théâtre ## -->
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_didascaly')]|text:span[starts-with(@text:style-name,'TEI_didascaly-inline')]">
	<stage>
        <xsl:if test="local-name()='span'">
            <xsl:attribute name="rend">inline</xsl:attribute>
        </xsl:if>
        <xsl:copy-of select="@rendition"/>
		<xsl:apply-templates/>
	</stage>
</xsl:template>

<xsl:template match="text:p[@text:style-name='TEI_replica']">
    <xsl:for-each-group select="node()" group-ending-with="text:line-break">
        <p>
            <xsl:copy-of select="parent::*:p[@text:style-name='TEI_replica']/@rendition"/>
            <xsl:apply-templates select="current-group()"/>
        </p>
    </xsl:for-each-group>
</xsl:template>

<xsl:template match="text:p[@text:style-name='TEI_versifiedreplica']">
    <xsl:for-each-group select="node()" group-ending-with="text:line-break">
        <l>
            <xsl:copy-of select="parent::*:p[@text:style-name='TEI_versifiedreplica']/@rendition"/>
            <xsl:variable name="lineNum" select="."/>
            <xsl:if test="$lineNum/local-name()='span' and $lineNum/@text:style-name='TEI_versenumber-inline'">
                <xsl:attribute name="n">
                    <xsl:analyze-string select="." regex="(\d+)">
                        <xsl:matching-substring><xsl:value-of select="."/></xsl:matching-substring>
                        <xsl:non-matching-substring></xsl:non-matching-substring>
                    </xsl:analyze-string>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates select="current-group()"/>
        </l>
    </xsl:for-each-group>
</xsl:template>

<!-- ### linguistique ### -->
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_linguistic_example')]">
    <xsl:if test="child::text:span[@text:style-name='TEI_linguistic_num']">
        <num><xsl:copy-of select="@rendition"/><xsl:value-of select="child::text:span[@text:style-name='TEI_linguistic_num']"/></num>
    </xsl:if>
    <quote type="example">
        <xsl:copy-of select="@xml:lang|@rendition"/>
        <xsl:choose>
            <xsl:when test="descendant::text:tab">
                <xsl:variable name="nodetoselect"><xsl:copy-of select="node()[not(self::text:span[starts-with(@text:style-name,'TEI_linguistic_num')])]"/></xsl:variable>
                <xsl:variable name="nodetoparse">
                    <xsl:choose>
                        <xsl:when test="$nodetoselect/child::node()[1][local-name()='tab']"><xsl:copy-of select="$nodetoselect/node()[position() &gt; 1]"/></xsl:when>
                        <xsl:otherwise><xsl:copy-of select="$nodetoselect"/></xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:for-each-group select="$nodetoparse/node()" group-ending-with="text:tab">
                    <seg>
                        <xsl:apply-templates select="current-group()"/>
                    </seg>
                </xsl:for-each-group>
            </xsl:when>
            <xsl:otherwise>
                <seg><xsl:apply-templates/></seg>
            </xsl:otherwise>
        </xsl:choose>
    </quote>
</xsl:template>
    
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_linguistic_gloss')]">
    <gloss>
        <xsl:copy-of select="@rendition"/>
        <xsl:choose>
            <xsl:when test="descendant::text:tab">
                <xsl:variable name="nodetoselect"><xsl:copy-of select="node()[not(self::text:span[starts-with(@text:style-name,'TEI_linguistic_num')])]"/></xsl:variable>
                <xsl:variable name="nodetoparse">
                    <xsl:choose>
                        <xsl:when test="$nodetoselect/child::node()[1][local-name()='tab']"><xsl:copy-of select="$nodetoselect/node()[position() &gt; 1]"/></xsl:when>
                        <xsl:otherwise><xsl:copy-of select="$nodetoselect"/></xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:for-each-group select="$nodetoparse/node()" group-ending-with="text:tab">
                    <seg>
                        <xsl:apply-templates select="current-group()"/>
                    </seg>
                </xsl:for-each-group>
            </xsl:when>
            <xsl:otherwise>
                <seg><xsl:apply-templates/></seg>
            </xsl:otherwise>
        </xsl:choose>
    </gloss>
</xsl:template>
    
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_linguistic_translation')]">
    <quote type="trl">
        <xsl:copy-of select="@rendition"/>
        <xsl:apply-templates/>
    </quote>
</xsl:template>
    
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_linguistic_label')]">
    <label>
        <xsl:copy-of select="@rendition"/>
        <xsl:if test="child::text:span[@text:style-name='TEI_linguistic_num']">
            <num><xsl:value-of select="child::text:span[@text:style-name='TEI_linguistic_num']"/></num>
        </xsl:if>
        <xsl:apply-templates/>
    </label>
</xsl:template>

<xsl:template match="text:span[@text:style-name='TEI_linguistic_num']"/>
    
<xsl:template match="text:span[@text:style-name='TEI_linguistic_lang-inline']">
    <lang><xsl:apply-templates/></lang>
</xsl:template>
 
<xsl:template match="text:p[starts-with(@text:style-name,'TEI_linguistic_lang')]">
    <xsl:if test="child::text:span[@text:style-name='TEI_linguistic_num']">
        <num><xsl:value-of select="child::text:span[@text:style-name='TEI_linguistic_num']"/></num>
    </xsl:if>
    <lang>
        <xsl:apply-templates/>
    </lang>
</xsl:template>

</xsl:stylesheet>